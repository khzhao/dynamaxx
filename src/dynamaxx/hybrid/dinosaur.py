# Copyright 2026 dynamaxx

"""Concrete additive-correction bridge for Dinosaur primitive equations."""

from dataclasses import dataclass, field, replace
from typing import Any, cast

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.data.weatherbench2 import WeatherBench2Source
from dynamaxx.dycore.models.dinosaur import adapter as dinosaur_adapter
from dynamaxx.dycore.models.dinosaur import (
    radiation,
    time_integration,
    units,
)
from dynamaxx.dycore.models.dinosaur.adapter import (
    DinosaurPrimitiveEquationsDycoreModel,
)
from dynamaxx.dycore.models.dinosaur.channels import (
    SPECIFIC_HUMIDITY_VARIABLE,
    TEN_METER_U_WIND_VARIABLE,
    TWO_METER_TEMPERATURE_VARIABLE,
    has_pressure_level_stack,
    infer_dinosaur_pressure_levels,
    supported_output_variables,
)
from dynamaxx.dycore.models.dinosaur.coordinates import grid_metadata
from dynamaxx.dycore.registry import create_dycore_model
from dynamaxx.training.corrector import ColumnResidualMLP
from dynamaxx.utils.consts import WEATHERBENCH2_ERA5_1P5DEG_6H_PATH
from dynamaxx.weather import WeatherState


@jax.tree_util.register_pytree_node_class
@dataclass(frozen=True)
class DinosaurNodalTendency:
    """Additive prognostic tendency fields in Dinosaur nodal coordinates."""

    vorticity: jax.Array
    divergence: jax.Array
    temperature_variation: jax.Array
    log_surface_pressure: jax.Array
    specific_humidity: jax.Array

    def tree_flatten(self):
        """Return dynamic children for JAX transformations."""
        return (
            self.vorticity,
            self.divergence,
            self.temperature_variation,
            self.log_surface_pressure,
            self.specific_humidity,
        ), None

    @classmethod
    def tree_unflatten(cls, auxiliary_data, children):
        """Reconstruct a nodal tendency from JAX PyTree children."""
        del auxiliary_data
        return cls(*children)


@jax.tree_util.register_pytree_node_class
@dataclass(frozen=True)
class DinosaurHybridCoreState:
    """Complete differentiable carry for the optimized Dinosaur configuration."""

    atmosphere: Any
    skin: tuple[jax.Array, jax.Array]
    equilibrium_temperature_offset: jax.Array
    ocean_temperature_anchor: jax.Array
    radiation_time_offset: jax.Array
    initial_surface_values: jax.Array
    raw_surface_values: jax.Array
    elapsed_seconds: jax.Array

    def tree_flatten(self):
        """Return dynamic children for JAX transformations."""
        return (
            self.atmosphere,
            self.skin,
            self.equilibrium_temperature_offset,
            self.ocean_temperature_anchor,
            self.radiation_time_offset,
            self.initial_surface_values,
            self.raw_surface_values,
            self.elapsed_seconds,
        ), None

    @classmethod
    def tree_unflatten(cls, auxiliary_data, children):
        """Reconstruct a core state from JAX PyTree children."""
        del auxiliary_data
        return cls(*children)


@dataclass(frozen=True)
class DinosaurNeuralCorrector:
    """Adapt flat column-MLP outputs to named Dinosaur tendency fields."""

    network: ColumnResidualMLP
    layer_count: int

    def __post_init__(self):
        if self.layer_count < 1:
            raise ValueError("layer_count must be positive")
        expected_output_size = 4 * self.layer_count + 1
        if self.network.output_size != expected_output_size:
            raise ValueError(
                f"network output_size must be {expected_output_size}; "
                f"received {self.network.output_size}"
            )

    def __call__(
        self,
        parameters: Any,
        inputs: jax.Array,
    ) -> DinosaurNodalTendency:
        """Predict and unpack one tendency at every horizontal column."""
        outputs = self.network(parameters, inputs)
        layer_count = self.layer_count
        vorticity = jnp.moveaxis(outputs[..., :layer_count], -1, 0)
        divergence = jnp.moveaxis(
            outputs[..., layer_count : 2 * layer_count],
            -1,
            0,
        )
        temperature_variation = jnp.moveaxis(
            outputs[..., 2 * layer_count : 3 * layer_count],
            -1,
            0,
        )
        specific_humidity = jnp.moveaxis(
            outputs[..., 3 * layer_count : 4 * layer_count],
            -1,
            0,
        )
        log_surface_pressure = jnp.moveaxis(
            outputs[..., 4 * layer_count :],
            -1,
            0,
        )
        return DinosaurNodalTendency(
            vorticity=vorticity,
            divergence=divergence,
            temperature_variation=temperature_variation,
            log_surface_pressure=log_surface_pressure,
            specific_humidity=specific_humidity,
        )


@dataclass(frozen=True)
class DinosaurNeuralDecoder:
    """Apply a learned nodal column residual to pressure-level observables."""

    network: ColumnResidualMLP
    output_variables: tuple[str, ...]
    include_raw_observation: bool = False

    def __post_init__(self):
        output_variables = tuple(map(str, self.output_variables))
        if self.network.output_size != len(output_variables):
            raise ValueError(
                "decoder output size must match the number of output variables"
            )
        object.__setattr__(self, "output_variables", output_variables)

    def __call__(
        self,
        parameters: Any,
        inputs: jax.Array,
        raw_observation: WeatherState,
    ) -> WeatherState:
        """Add one bounded learned residual independently at every column."""
        if raw_observation.variables != self.output_variables:
            raise ValueError("decoder variables do not match raw observation")
        decoder_inputs = inputs
        if self.include_raw_observation:
            raw_column_values = jnp.moveaxis(raw_observation.values, 0, -1)
            if raw_column_values.shape[:-1] != inputs.shape[:-1]:
                raise ValueError(
                    "raw observation grid must match the decoder input grid"
                )
            decoder_inputs = jnp.concatenate(
                (inputs, raw_column_values),
                axis=-1,
            )
        column_residual = self.network(parameters, decoder_inputs)
        residual = jnp.moveaxis(column_residual, -1, 0)
        return raw_observation.with_values(raw_observation.values + residual)


@dataclass(frozen=True)
class DinosaurHybridCore:
    """Prepared differentiable core matching one frozen Dinosaur model."""

    model: DinosaurPrimitiveEquationsDycoreModel
    longitude: np.ndarray
    latitude: np.ndarray
    input_variables: tuple[str, ...]
    data_path: str = WEATHERBENCH2_ERA5_1P5DEG_6H_PATH
    fallback_to_centered_sil3_on_nonfinite: bool = True
    _atmosphere_initializer: Any = field(
        init=False,
        repr=False,
        compare=False,
    )

    def __post_init__(self):
        longitude = np.asarray(self.longitude, dtype=np.float64)
        latitude = np.asarray(self.latitude, dtype=np.float64)
        input_variables = tuple(map(str, self.input_variables))
        pressure_levels_hpa = infer_dinosaur_pressure_levels(input_variables)
        grid = grid_metadata(
            longitude=longitude,
            latitude=latitude,
            layer_count=len(pressure_levels_hpa),
            spectral_wavenumbers=self.model.spectral_wavenumbers,
        )
        physics_specs = units.SimUnits.from_si()
        reference_temperature = dinosaur_adapter._reference_temperature(
            layer_count=len(pressure_levels_hpa),
            temperature_kelvin=self.model.reference_temperature_kelvin,
        )
        has_humidity = has_pressure_level_stack(
            input_variables,
            SPECIFIC_HUMIDITY_VARIABLE,
            pressure_levels_hpa,
        )
        if not has_humidity:
            raise ValueError(
                "hybrid training requires specific humidity at every pressure level"
            )
        output_variables = supported_output_variables(
            input_variables,
            pressure_levels_hpa=pressure_levels_hpa,
            has_humidity=has_humidity,
            requested_variables=self.model.output_variables,
        )
        land_fraction, terrain_height = self._load_static_fields(
            longitude,
            latitude,
        )
        dinosaur_land_fraction = dinosaur_adapter._to_dinosaur_latitude_order(
            land_fraction,
            grid.latitude_reversed,
        )
        land_weight = jnp.asarray(dinosaur_land_fraction, dtype=jnp.float32)
        ocean_weight = 1.0 - land_weight
        dinosaur_terrain_height = dinosaur_adapter._to_dinosaur_latitude_order(
            terrain_height,
            grid.latitude_reversed,
        )
        solar_model = radiation.SolarRadiation(
            coords=grid.coords,
            physics_specs=physics_specs,
            reference_datetime=radiation.WB_REFERENCE_DATETIME,
        )
        normalized_solar_model = radiation.SolarRadiation.normalized(
            coords=grid.coords,
            physics_specs=physics_specs,
            reference_datetime=radiation.WB_REFERENCE_DATETIME,
        )
        object.__setattr__(self, "longitude", longitude)
        object.__setattr__(self, "latitude", latitude)
        object.__setattr__(self, "input_variables", input_variables)
        object.__setattr__(self, "pressure_levels_hpa", pressure_levels_hpa)
        object.__setattr__(self, "grid", grid)
        object.__setattr__(self, "coords", grid.coords)
        object.__setattr__(self, "physics_specs", physics_specs)
        object.__setattr__(self, "reference_temperature", reference_temperature)
        object.__setattr__(self, "output_variables", output_variables)
        object.__setattr__(self, "land_fraction", jnp.asarray(land_fraction))
        object.__setattr__(self, "land_weight", land_weight)
        object.__setattr__(self, "ocean_weight", ocean_weight)
        object.__setattr__(
            self,
            "terrain_height_meters",
            jnp.asarray(dinosaur_terrain_height, dtype=jnp.float32),
        )
        object.__setattr__(self, "solar_model", solar_model)
        object.__setattr__(self, "normalized_solar_model", normalized_solar_model)
        surface_variables = tuple(
            variable
            for variable in (
                TWO_METER_TEMPERATURE_VARIABLE,
                TEN_METER_U_WIND_VARIABLE,
            )
            if variable in input_variables and variable in output_variables
        )
        object.__setattr__(self, "surface_variables", surface_variables)
        object.__setattr__(
            self,
            "_atmosphere_initializer",
            jax.jit(self._initialize_atmosphere_uncompiled),
        )

    def _load_static_fields(
        self,
        longitude: np.ndarray,
        latitude: np.ndarray,
    ) -> tuple[jax.Array, jax.Array]:
        """Load required land fraction and terrain from the configured source."""
        source = WeatherBench2Source(path=self.data_path)
        source_longitude, source_latitude = source.spatial_coordinates(year=2018)
        if not (
            np.array_equal(source_longitude, longitude)
            and np.array_equal(source_latitude, latitude)
        ):
            raise ValueError("WeatherBench2 constants do not match the model grid")
        constants = source.read_constants(("land_sea_mask", "geopotential_at_surface"))
        land_fraction = jnp.clip(constants[0], 0.0, 1.0)
        terrain_height = constants[1] / 9.80665
        if not bool(jnp.all(jnp.isfinite(land_fraction))):
            raise ValueError("land_sea_mask contains non-finite values")
        if not bool(jnp.all(jnp.isfinite(terrain_height))):
            raise ValueError("surface geopotential contains non-finite values")
        return land_fraction, terrain_height

    @property
    def inner_step_seconds(self) -> float:
        """Duration of one completed Dinosaur integration step."""
        return float(self.model.inner_step_seconds)

    @property
    def layer_count(self) -> int:
        """Number of Dinosaur sigma layers."""
        return len(self.pressure_levels_hpa)

    @property
    def input_feature_count(self) -> int:
        """Number of scalar values supplied to the MLP at each column."""
        prognostic_count = 4 * self.layer_count + 1
        return 3 * prognostic_count + 2 + 2 + 4 + 4 + 1

    @property
    def output_feature_count(self) -> int:
        """Number of scalar tendency values emitted at each column."""
        return 4 * self.layer_count + 1

    @property
    def conservative_output_scale(self) -> jax.Array:
        """Conservative native-unit tendency scales for zero-start training."""
        second_factor = dinosaur_adapter._nondimensionalize_seconds(
            self.physics_specs,
            1.0,
        )
        vorticity_rate_factor = (
            dinosaur_adapter._unit_factor(
                self.physics_specs,
                "1 / second",
            )
            / second_factor
        )
        temperature_rate_factor = (
            dinosaur_adapter._unit_factor(
                self.physics_specs,
                "kelvin",
            )
            / second_factor
        )
        scalar_rate_factor = 1.0 / second_factor
        return jnp.asarray(
            [
                *([1.0e-10 * vorticity_rate_factor] * self.layer_count),
                *([1.0e-10 * vorticity_rate_factor] * self.layer_count),
                *([1.0e-5 * temperature_rate_factor] * self.layer_count),
                *([1.0e-9 * scalar_rate_factor] * self.layer_count),
                1.0e-7 * scalar_rate_factor,
            ],
            dtype=jnp.float32,
        )

    def _base_equation(
        self,
        *,
        physics_specs: Any,
        equilibrium_temperature_offset: jax.Array,
        ocean_temperature_anchor: jax.Array | None,
        use_anticipated_pv_flux: bool,
    ) -> Any:
        """Build the production explicit/implicit equation configuration."""
        _, sin_latitude = self.coords.horizontal.nodal_mesh
        coriolis_parameter = 2.0 * self.physics_specs.angular_velocity * sin_latitude
        step = dinosaur_adapter._nondimensionalize_seconds(
            self.physics_specs,
            self.inner_step_seconds,
        )
        equation = dinosaur_adapter._primitive_equation(
            reference_temperature=self.reference_temperature,
            orography=jnp.zeros(
                self.coords.horizontal.modal_shape,
                dtype=jnp.float32,
            ),
            coords=self.coords,
            physics_specs=physics_specs,
            include_vertical_advection=self.model.include_vertical_advection,
            humidity_key=(
                SPECIFIC_HUMIDITY_VARIABLE
                if self.model.use_humidity_in_dynamics
                else None
            ),
            temperature_tendency_formulation=(
                self.model.temperature_tendency_formulation
            ),
            use_horizontal_semilagrangian_theta_transport=(
                self.model.use_horizontal_semilagrangian_theta_transport
            ),
            use_midpoint_semilagrangian_theta_departure=(
                self.model.use_midpoint_semilagrangian_theta_departure
            ),
            use_dry_static_energy_hsl_transport=(
                self.model.use_dry_static_energy_hsl_transport
            ),
            use_layer_mass_weighted_dse_hsl_transport=(
                self.model.use_layer_mass_weighted_dse_hsl_transport
            ),
            use_pressure_ramped_vertical_dse_increment=(
                self.model.use_pressure_ramped_vertical_dse_increment
            ),
            use_anticipated_pv_flux=use_anticipated_pv_flux,
            anticipated_pv_step_seconds=(step if use_anticipated_pv_flux else 0.0),
            anticipated_pv_coriolis_parameter=(
                coriolis_parameter if use_anticipated_pv_flux else None
            ),
            horizontal_semilagrangian_theta_transport_step=step,
        )
        if self.model.apply_weak_held_suarez_relaxation:
            equation = dinosaur_adapter._compose_weak_held_suarez_equation(
                equation=equation,
                coords=self.coords,
                physics_specs=physics_specs,
                reference_temperature=self.reference_temperature,
                kf_per_day=self.model.weak_held_suarez_kf_per_day,
                ka_timescale_days=self.model.weak_held_suarez_ka_timescale_days,
                ks_timescale_days=self.model.weak_held_suarez_ks_timescale_days,
                equilibrium_temperature_offset=equilibrium_temperature_offset,
            )
        if ocean_temperature_anchor is not None:
            equation = dinosaur_adapter._compose_ocean_bulk_sensible_heat_flux_equation(
                equation=equation,
                coords=self.coords,
                physics_specs=physics_specs,
                reference_temperature=self.reference_temperature,
                ocean_weight=self.ocean_weight,
                temperature_anchor=ocean_temperature_anchor,
                step_seconds=step,
            )
        return equation

    def _horizontal_filter(self, physics_specs: Any) -> Any:
        """Build the production scale-aware horizontal diffusion filter."""
        return dinosaur_adapter._horizontal_diffusion_step_filter(
            coords=self.coords,
            physics_specs=physics_specs,
            step_seconds=dinosaur_adapter._nondimensionalize_seconds(
                physics_specs,
                self.inner_step_seconds,
            ),
            tau_seconds=self.model.horizontal_diffusion_tau_seconds,
            order=self.model.horizontal_diffusion_order,
        )

    def _initialize_atmosphere_uncompiled(
        self,
        state: Any,
        offset: jax.Array,
    ) -> Any:
        """Construct and apply the frozen digital-filter initialization."""
        if not self.model.apply_digital_filter_initialization:
            return state
        equation = self._base_equation(
            physics_specs=self.physics_specs,
            equilibrium_temperature_offset=offset,
            ocean_temperature_anchor=None,
            use_anticipated_pv_flux=False,
        )
        filters = [self._horizontal_filter(self.physics_specs)]
        initializer = time_integration.digital_filter_initialization(
            equation,
            self.model._ode_solver(),
            filters,
            time_span=dinosaur_adapter._nondimensionalize_seconds(
                self.physics_specs,
                self.model.digital_filter_time_span_seconds,
            ),
            cutoff_period=dinosaur_adapter._nondimensionalize_seconds(
                self.physics_specs,
                self.model.digital_filter_cutoff_seconds,
            ),
            dt=dinosaur_adapter._nondimensionalize_seconds(
                self.physics_specs,
                self.inner_step_seconds,
            ),
        )
        return initializer(state)

    def _initialize_atmosphere(self, state: Any, offset: jax.Array) -> Any:
        """Apply the reusable compiled digital-filter initialization."""
        return self._atmosphere_initializer(state, offset)

    def initialize(
        self,
        weather_state: WeatherState,
        initial_time: np.datetime64,
    ) -> DinosaurHybridCoreState:
        """Encode one truth state and initialize all frozen auxiliary memory."""
        if weather_state.variables != self.input_variables:
            raise ValueError("weather_state variables do not match the prepared core")
        atmosphere = dinosaur_adapter.weather_state_to_dinosaur_state(
            weather_state,
            coords=self.coords,
            pressure_levels_hpa=self.pressure_levels_hpa,
            latitude_reversed=self.grid.latitude_reversed,
            physics_specs=self.physics_specs,
            reference_temperature=self.reference_temperature,
            include_humidity=True,
            use_log_pressure_initialization=self.model.use_log_pressure_initialization,
            use_hydrostatic_temperature_initialization=(
                self.model.use_hydrostatic_temperature_initialization
            ),
            use_layer_mean_hydrostatic_temperature_initialization=(
                self.model.use_layer_mean_hydrostatic_temperature_initialization
            ),
            initialize_sim_time=True,
        )
        equilibrium_temperature_offset = (
            dinosaur_adapter._analysis_offset_weak_held_suarez_equilibrium(
                atmosphere,
                coords=self.coords,
                physics_specs=self.physics_specs,
                reference_temperature=self.reference_temperature,
            )
        )
        ocean_temperature_anchor = (
            dinosaur_adapter._ocean_bulk_sensible_heat_flux_temperature_anchor(
                weather_state,
                dinosaur_state=atmosphere,
                coords=self.coords,
                latitude_reversed=self.grid.latitude_reversed,
                physics_specs=self.physics_specs,
                reference_temperature=self.reference_temperature,
            )
        )
        if ocean_temperature_anchor is None:
            raise ValueError("could not initialize the ocean temperature anchor")
        atmosphere = self._initialize_atmosphere(
            atmosphere,
            equilibrium_temperature_offset,
        )
        skin = dinosaur_adapter._land_skin_reservoir_initial_skin(
            atmosphere,
            coords=self.coords,
            reference_temperature=self.reference_temperature,
        )
        analyzed_skin_temperature = dinosaur_adapter._analysis_2m_land_skin_temperature(
            weather_state,
            spatial_shape=self.coords.horizontal.nodal_shape,
            latitude_reversed=self.grid.latitude_reversed,
            physics_specs=self.physics_specs,
        )
        skin = dinosaur_adapter._analysis_2m_initialized_land_skin(
            skin,
            analyzed_temperature=analyzed_skin_temperature,
            land_weight=self.land_weight,
        )
        radiation_time_offset = (
            dinosaur_adapter._radiative_land_skin_initial_time_offset(
                initial_time,
                reference_time=np.datetime64(radiation.WB_REFERENCE_DATETIME, "ns"),
                physics_specs=self.physics_specs,
            )
        )
        initial_surface_state = weather_state.select(self.surface_variables)
        provisional_state = DinosaurHybridCoreState(
            atmosphere=atmosphere,
            skin=skin,
            equilibrium_temperature_offset=equilibrium_temperature_offset,
            ocean_temperature_anchor=ocean_temperature_anchor,
            radiation_time_offset=radiation_time_offset,
            initial_surface_values=initial_surface_state.values,
            raw_surface_values=jnp.zeros_like(initial_surface_state.values),
            elapsed_seconds=jnp.asarray(0.0, dtype=jnp.float32),
        )
        raw_output = self._decode_atmosphere(provisional_state)
        raw_surface_values = raw_output.select(self.surface_variables).values
        return replace(provisional_state, raw_surface_values=raw_surface_values)

    def corrector_inputs(self, state: DinosaurHybridCoreState) -> jax.Array:
        """Build normalized-ready causal nodal column features."""
        atmosphere = state.atmosphere
        humidity = atmosphere.tracers[SPECIFIC_HUMIDITY_VARIABLE]
        modal_prognostics = jnp.concatenate(
            (
                atmosphere.vorticity,
                atmosphere.divergence,
                atmosphere.temperature_variation,
                humidity,
                atmosphere.log_surface_pressure,
            ),
            axis=0,
        )
        nodal_prognostics = self.coords.horizontal.to_nodal(modal_prognostics)
        zonal_gradient, meridional_gradient = self.coords.horizontal.cos_lat_grad(
            modal_prognostics,
            clip=False,
        )
        nodal_gradients = jnp.concatenate(
            (
                self.coords.horizontal.to_nodal(zonal_gradient),
                self.coords.horizontal.to_nodal(meridional_gradient),
            ),
            axis=0,
        )
        longitude, sin_latitude = self.coords.horizontal.nodal_mesh
        cosine_latitude = jnp.sqrt(jnp.maximum(1.0 - sin_latitude**2, 0.0))
        geometry = jnp.stack(
            (
                jnp.sin(longitude),
                jnp.cos(longitude),
                sin_latitude,
                cosine_latitude,
            )
        )
        absolute_time = state.radiation_time_offset + atmosphere.sim_time
        orbital_time = self.normalized_solar_model.time_to_orbital_time(absolute_time)
        time_features = jnp.broadcast_to(
            jnp.asarray(
                (
                    jnp.sin(orbital_time.synodic_phase),
                    jnp.cos(orbital_time.synodic_phase),
                    jnp.sin(orbital_time.orbital_phase),
                    jnp.cos(orbital_time.orbital_phase),
                )
            )[:, jnp.newaxis, jnp.newaxis],
            (4, *self.coords.horizontal.nodal_shape),
        )
        solar_flux = self.normalized_solar_model.radiation_flux(absolute_time)[
            jnp.newaxis
        ]
        surface_memory = jnp.stack(state.skin)
        static_surface = jnp.stack((self.terrain_height_meters, self.land_weight))
        features = jnp.concatenate(
            (
                nodal_prognostics,
                nodal_gradients,
                surface_memory,
                static_surface,
                geometry,
                time_features,
                solar_flux,
            ),
            axis=0,
        )
        return jnp.moveaxis(features, 0, -1)

    def _remove_area_mean(self, values: jax.Array) -> jax.Array:
        """Project nodal fields onto the globally mean-free subspace."""
        weights = jnp.asarray(
            self.coords.horizontal.quadrature_weights,
            dtype=values.dtype,
        )
        mean = jnp.sum(values * weights, axis=(-2, -1), keepdims=True) / jnp.sum(
            weights
        )
        return values - mean

    def to_native_tendency(
        self,
        state: DinosaurHybridCoreState,
        nodal_tendency: DinosaurNodalTendency,
    ) -> Any:
        """Project nodal neural tendencies into clipped Dinosaur modes."""
        del state
        tendency = dinosaur_adapter._primitive_equation_state(
            vorticity=self.coords.horizontal.to_modal(
                self._remove_area_mean(nodal_tendency.vorticity)
            ),
            divergence=self.coords.horizontal.to_modal(
                self._remove_area_mean(nodal_tendency.divergence)
            ),
            temperature_variation=self.coords.horizontal.to_modal(
                nodal_tendency.temperature_variation
            ),
            log_surface_pressure=self.coords.horizontal.to_modal(
                self._remove_area_mean(nodal_tendency.log_surface_pressure)
            ),
            tracers={
                SPECIFIC_HUMIDITY_VARIABLE: self.coords.horizontal.to_modal(
                    nodal_tendency.specific_humidity
                )
            },
            sim_time=jnp.asarray(0.0, dtype=jnp.float32),
        )
        return self.coords.horizontal.clip_wavenumbers(tendency)

    def _step_function(
        self,
        state: DinosaurHybridCoreState,
        additive_tendency: Any,
    ) -> Any:
        """Build one production SIL3 step with a fixed neural explicit term."""
        rollout_physics_specs = replace(self.physics_specs, angular_velocity=0.0)
        equation = self._base_equation(
            physics_specs=rollout_physics_specs,
            equilibrium_temperature_offset=state.equilibrium_temperature_offset,
            ocean_temperature_anchor=state.ocean_temperature_anchor,
            use_anticipated_pv_flux=True,
        )
        neural_equation = time_integration.ExplicitODE.from_functions(
            lambda _: additive_tendency
        )
        equation = time_integration.compose_equations((equation, neural_equation))
        step = dinosaur_adapter._nondimensionalize_seconds(
            rollout_physics_specs,
            self.inner_step_seconds,
        )
        step_function = self.model._ode_solver(
            fallback_to_centered_on_nonfinite=(
                self.fallback_to_centered_sil3_on_nonfinite
            )
        )(equation, time_step=step)
        filters = [self._horizontal_filter(rollout_physics_specs)]
        filters.extend(
            (
                dinosaur_adapter._tropical_wtg_mass_dse_relaxation_step_filter(
                    coords=self.coords,
                    physics_specs=self.physics_specs,
                    reference_temperature=self.reference_temperature,
                    step_seconds=step,
                ),
                dinosaur_adapter._ekman_coupled_surface_step_filter(
                    coords=self.coords,
                    physics_specs=self.physics_specs,
                    reference_temperature=self.reference_temperature,
                    step_seconds=step,
                    use_coriolis_scaled_ekman_depth=True,
                ),
                dinosaur_adapter._orographic_lift_theta_tendency_step_filter(
                    coords=self.coords,
                    physics_specs=self.physics_specs,
                    reference_temperature=self.reference_temperature,
                    terrain_height_meters=self.terrain_height_meters,
                    step_seconds=step,
                    use_depth_weighted_wind=True,
                ),
                dinosaur_adapter._terrain_work_form_drag_heating_step_filter(
                    coords=self.coords,
                    physics_specs=self.physics_specs,
                    terrain_height_meters=self.terrain_height_meters,
                    step_seconds=step,
                ),
                dinosaur_adapter._theta_layer_mean_recenter_step_filter(
                    coords=self.coords,
                    physics_specs=self.physics_specs,
                    reference_temperature=self.reference_temperature,
                ),
            )
        )
        step_function = time_integration.step_with_filters(step_function, filters)
        step_function = dinosaur_adapter._symmetric_exact_coriolis_rotation_step(
            step_function,
            coords=self.coords,
            physics_specs=self.physics_specs,
            step_seconds=step,
        )
        return dinosaur_adapter._land_skin_reservoir_step(
            step_function,
            coords=self.coords,
            physics_specs=self.physics_specs,
            reference_temperature=self.reference_temperature,
            land_weight=self.land_weight,
            step_seconds_si=self.inner_step_seconds,
            solar_radiation_model=self.solar_model,
            radiation_time_offset=state.radiation_time_offset,
        )

    def advance_one_inner_step(
        self,
        state: DinosaurHybridCoreState,
        additive_tendency: Any,
    ) -> DinosaurHybridCoreState:
        """Advance one full dycore step with the neural tendency."""
        step_function = self._step_function(state, additive_tendency)
        atmosphere, skin = step_function((state.atmosphere, state.skin))
        return replace(
            state,
            atmosphere=atmosphere,
            skin=skin,
            elapsed_seconds=state.elapsed_seconds + self.inner_step_seconds,
        )

    def _decode_atmosphere(self, state: DinosaurHybridCoreState) -> WeatherState:
        """Decode one native atmosphere without applying residual output memory."""
        trajectory = jax.tree_util.tree_map(
            lambda value: value[jnp.newaxis],
            state.atmosphere,
        )
        decoded = dinosaur_adapter.dinosaur_state_to_weather_state(
            trajectory,
            coords=self.coords,
            pressure_levels_hpa=self.pressure_levels_hpa,
            latitude_reversed=self.grid.latitude_reversed,
            physics_specs=self.physics_specs,
            reference_temperature=self.reference_temperature,
            output_variables=self.output_variables,
            use_surface_layer_richardson_10m_wind_diagnostic=True,
            use_bulk_richardson_2m_temperature_diagnostic=True,
            use_pressure_thickness_weighted_ri2m_temperature=True,
            use_prognostic_skin_ri2m_lower_boundary=True,
            prognostic_skin_temperature=state.skin[0][jnp.newaxis],
            land_weight=self.land_weight,
            use_ocean_anchor_ri2m_lower_boundary=True,
            ocean_temperature_anchor=state.ocean_temperature_anchor,
        )
        return WeatherState(values=decoded.values[0], variables=decoded.variables)

    def decode(self, state: DinosaurHybridCoreState) -> WeatherState:
        """Decode current observables and apply frozen surface residual memory."""
        current = self._decode_atmosphere(state)
        if not self.model.apply_near_surface_residual_correction:
            return current
        raw_proxy_values = current.values
        for surface_index, variable in enumerate(self.surface_variables):
            output_index = int(current.variable_indices((variable,))[0])
            raw_proxy_values = raw_proxy_values.at[output_index].set(
                state.raw_surface_values[surface_index]
            )
        trajectory = WeatherState(
            values=jnp.stack((raw_proxy_values, current.values)),
            variables=current.variables,
        )
        initial_surface_state = WeatherState(
            values=state.initial_surface_values,
            variables=self.surface_variables,
        )
        corrected = (
            dinosaur_adapter._apply_scale_separated_near_surface_residual_correction(
                trajectory,
                initial_state=initial_surface_state,
                lead_steps=(1,),
                lead_hours=cast(
                    tuple[int, ...],
                    (state.elapsed_seconds / 3600.0,),
                ),
                decay_hours=self.model.near_surface_residual_decay_hours,
                use_stability_aware_decay=(
                    self.model.use_stability_aware_near_surface_residual_decay
                ),
                horizontal_grid=self.coords.horizontal,
                latitude_reversed=self.grid.latitude_reversed,
                land_sea_fraction=self.land_fraction,
                use_land_ocean_low_mode_t2m_memory=(
                    self.model.use_land_ocean_low_mode_t2m_memory
                ),
            )
        )
        return WeatherState(values=corrected.values[0], variables=corrected.variables)


@dataclass(frozen=True)
class DinosaurHybridCoreFactory:
    """Build a prepared Dinosaur bridge from a registered dycore name."""

    dycore_name: str
    data_path: str = WEATHERBENCH2_ERA5_1P5DEG_6H_PATH
    fallback_to_centered_sil3_on_nonfinite: bool = True

    def __call__(
        self,
        *,
        longitude: np.ndarray,
        latitude: np.ndarray,
        input_variables: tuple[str, ...],
    ) -> DinosaurHybridCore:
        """Prepare the selected frozen Dinosaur configuration."""
        model = create_dycore_model(self.dycore_name)
        if not isinstance(model, DinosaurPrimitiveEquationsDycoreModel):
            raise ValueError(
                f"dycore {self.dycore_name!r} is not a Dinosaur primitive-equation model"
            )
        return DinosaurHybridCore(
            model=cast(DinosaurPrimitiveEquationsDycoreModel, model),
            longitude=longitude,
            latitude=latitude,
            input_variables=input_variables,
            data_path=self.data_path,
            fallback_to_centered_sil3_on_nonfinite=(
                self.fallback_to_centered_sil3_on_nonfinite
            ),
        )


def make_dinosaur_hybrid_core(
    *,
    dycore_name: str,
    longitude: np.ndarray,
    latitude: np.ndarray,
    input_variables: tuple[str, ...],
    data_path: str = WEATHERBENCH2_ERA5_1P5DEG_6H_PATH,
    fallback_to_centered_sil3_on_nonfinite: bool = True,
) -> DinosaurHybridCore:
    """Construct the internal prepared core used by training and public models."""
    return DinosaurHybridCoreFactory(
        dycore_name=dycore_name,
        data_path=data_path,
        fallback_to_centered_sil3_on_nonfinite=(fallback_to_centered_sil3_on_nonfinite),
    )(
        longitude=longitude,
        latitude=latitude,
        input_variables=input_variables,
    )

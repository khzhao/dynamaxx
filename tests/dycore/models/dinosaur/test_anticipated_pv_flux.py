# Copyright 2026 dynamaxx

from dataclasses import replace

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from dynamaxx.dycore.models.dinosaur import adapter as dinosaur_adapter
from dynamaxx.dycore.models.dinosaur import (
    coordinate_systems,
    primitive_equations,
    sigma_coordinates,
    spherical_harmonic,
    time_integration,
    units,
)
from dynamaxx.dycore.models.dinosaur.adapter import (
    DinosaurPrimitiveEquationsDycoreModel,
    _nondimensionalize_seconds,
    anticipated_pv_flux_dinosaur_dycore_model,
    zero_mean_radiative_land_skin_energy_dinosaur_dycore_model,
)


def _apvm_test_setup():
    physics_specs = units.SimUnits.from_si()
    horizontal_grid = spherical_harmonic.Grid(
        longitude_wavenumbers=3,
        total_wavenumbers=5,
        longitude_nodes=8,
        latitude_nodes=5,
        latitude_spacing="equiangular",
        radius=physics_specs.radius,
    )
    vertical_grid = sigma_coordinates.SigmaCoordinates(
        np.asarray([0.0, 0.25, 1.0], dtype=np.float32)
    )
    coords = coordinate_systems.CoordinateSystem(horizontal_grid, vertical_grid)
    state = primitive_equations.State(
        vorticity=(
            jnp.zeros(coords.modal_shape, dtype=jnp.float32)
            .at[:, 0, 1]
            .set(jnp.asarray([0.06, -0.04], dtype=jnp.float32))
            .at[:, 1, 2]
            .set(jnp.asarray([0.015, 0.025], dtype=jnp.float32))
        ),
        divergence=(
            jnp.zeros(coords.modal_shape, dtype=jnp.float32)
            .at[:, 1, 1]
            .set(jnp.asarray([0.04, 0.02], dtype=jnp.float32))
            .at[:, 2, 2]
            .set(jnp.asarray([-0.01, 0.015], dtype=jnp.float32))
        ),
        temperature_variation=(
            jnp.zeros(coords.modal_shape, dtype=jnp.float32)
            .at[:, 0, 0]
            .set(jnp.asarray([0.3, -0.2], dtype=jnp.float32))
        ),
        log_surface_pressure=(
            jnp.zeros(coords.surface_modal_shape, dtype=jnp.float32)
            .at[0, 0, 0]
            .set(0.02)
            .at[0, 1, 1]
            .set(0.01)
        ),
        tracers={
            "passive": (
                jnp.zeros(coords.modal_shape, dtype=jnp.float32)
                .at[:, 0, 1]
                .set(jnp.asarray([0.001, 0.002], dtype=jnp.float32))
            )
        },
        sim_time=jnp.asarray(2.0, dtype=jnp.float32),
    )
    _, sin_latitude = coords.horizontal.nodal_mesh
    physical_coriolis_parameter = 2.0 * physics_specs.angular_velocity * sin_latitude
    rollout_physics_specs = replace(physics_specs, angular_velocity=0.0)
    common_equation_kwargs = {
        "reference_temperature": np.full(vertical_grid.layers, 250.0),
        "orography": jnp.zeros(coords.horizontal.modal_shape, dtype=jnp.float32),
        "coords": coords,
        "physics_specs": rollout_physics_specs,
        "include_vertical_advection": False,
    }
    incumbent_equation = primitive_equations.PrimitiveEquationsSigma(
        **common_equation_kwargs
    )
    candidate_equation = primitive_equations.PrimitiveEquationsSigma(
        **common_equation_kwargs,
        use_anticipated_pv_flux=True,
        anticipated_pv_step_seconds=_nondimensionalize_seconds(
            physics_specs,
            900.0,
        ),
        anticipated_pv_coriolis_parameter=physical_coriolis_parameter,
    )
    return (
        coords,
        physics_specs,
        state,
        incumbent_equation,
        candidate_equation,
    )


def _replace_aux_state(aux_state, **updates):
    values = {
        "vorticity": aux_state.vorticity,
        "divergence": aux_state.divergence,
        "temperature_variation": aux_state.temperature_variation,
        "cos_lat_u": aux_state.cos_lat_u,
        "sigma_dot_explicit": aux_state.sigma_dot_explicit,
        "sigma_dot_full": aux_state.sigma_dot_full,
        "cos_lat_grad_log_sp": aux_state.cos_lat_grad_log_sp,
        "u_dot_grad_log_sp": aux_state.u_dot_grad_log_sp,
        "tracers": aux_state.tracers,
    }
    values.update(updates)
    return primitive_equations.DiagnosticStateSigma(**values)


def _assert_tree_array_equal(actual, expected):
    actual_leaves = jax.tree_util.tree_leaves(actual)
    expected_leaves = jax.tree_util.tree_leaves(expected)
    assert len(actual_leaves) == len(expected_leaves)
    for actual_leaf, expected_leaf in zip(actual_leaves, expected_leaves, strict=True):
        np.testing.assert_array_equal(actual_leaf, expected_leaf)


def test_apvm_factory_changes_only_name_and_selector():
    """The APVM factory changes only the incumbent name and selector."""
    candidate = anticipated_pv_flux_dinosaur_dycore_model()
    incumbent = zero_mean_radiative_land_skin_energy_dinosaur_dycore_model()

    assert candidate.name == "dino_rskin_apv"
    assert candidate.apply_anticipated_pv_flux
    assert not incumbent.apply_anticipated_pv_flux
    for field_name in candidate.__dataclass_fields__:
        if field_name in {"name", "apply_anticipated_pv_flux"}:
            continue
        assert getattr(candidate, field_name) == getattr(incumbent, field_name)


def test_apvm_layer_pv_uses_surface_pressure_and_sigma_thickness():
    """The layer PV denominator uses surface pressure and sigma thickness."""
    coords, _, state, _, equation = _apvm_test_setup()
    aux_state = primitive_equations.compute_diagnostic_state_sigma(state, coords)
    physical_coriolis_parameter = equation.anticipated_pv_coriolis_parameter
    absolute_vorticity = jnp.ones_like(aux_state.vorticity)
    diagnostic_aux_state = _replace_aux_state(
        aux_state,
        vorticity=absolute_vorticity - physical_coriolis_parameter,
    )

    layer_mass, layer_pv, valid_mass = equation._anticipated_pv_diagnostic(
        state,
        diagnostic_aux_state,
    )

    surface_pressure = jnp.exp(coords.horizontal.to_nodal(state.log_surface_pressure))
    sigma_thickness = jnp.asarray(
        coords.vertical.layer_thickness,
        dtype=surface_pressure.dtype,
    )[:, np.newaxis, np.newaxis]
    expected_mass = surface_pressure * sigma_thickness
    np.testing.assert_allclose(layer_mass, expected_mass, rtol=1e-6, atol=1e-6)
    np.testing.assert_allclose(layer_pv, 1.0 / expected_mass, rtol=1e-6, atol=1e-6)
    np.testing.assert_array_equal(valid_mass, jnp.ones_like(valid_mass, dtype=bool))
    np.testing.assert_allclose(
        layer_pv[0] / layer_pv[1],
        coords.vertical.layer_thickness[1] / coords.vertical.layer_thickness[0],
        rtol=1e-6,
        atol=1e-6,
    )


def test_apvm_flux_has_frozen_sign_and_zero_nodal_wind_work():
    """The frozen APVM sign produces a flux perpendicular to nodal wind."""
    coords, _, state, _, equation = _apvm_test_setup()
    aux_state = primitive_equations.compute_diagnostic_state_sigma(state, coords)

    flux_u, flux_v, delta_eta, diagnostics_valid = (
        equation._anticipated_pv_flux_components(state, aux_state)
    )
    layer_mass, layer_pv, _ = equation._anticipated_pv_diagnostic(state, aux_state)
    modal_pv = coords.horizontal.to_modal(layer_pv)
    nodal_cos_lat_grad_pv = coords.horizontal.to_nodal(
        coords.horizontal.cos_lat_grad(modal_pv, clip=False)
    )
    u, v = aux_state.cos_lat_u
    material_derivative = (
        u * nodal_cos_lat_grad_pv[0] + v * nodal_cos_lat_grad_pv[1]
    ) * coords.horizontal.sec2_lat
    expected_delta_eta = (
        -layer_mass * equation.anticipated_pv_step_seconds * material_derivative
    )

    assert bool(diagnostics_valid)
    np.testing.assert_allclose(delta_eta, expected_delta_eta, rtol=1e-6, atol=1e-6)
    np.testing.assert_allclose(
        flux_u,
        -v * expected_delta_eta * coords.horizontal.sec2_lat,
        rtol=1e-6,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        flux_v,
        u * expected_delta_eta * coords.horizontal.sec2_lat,
        rtol=1e-6,
        atol=1e-6,
    )
    assert float(jnp.sum(delta_eta * material_derivative)) < 0.0
    np.testing.assert_allclose(u * flux_u + v * flux_v, 0.0, atol=1e-7)


def test_constant_layer_pv_and_zero_wind_add_no_apvm_flux():
    """Constant layer PV and zero wind each produce no APVM correction."""
    coords, _, state, incumbent_equation, equation = _apvm_test_setup()
    aux_state = primitive_equations.compute_diagnostic_state_sigma(state, coords)
    layer_mass, _, _ = equation._anticipated_pv_diagnostic(state, aux_state)
    constant_layer_pv = jnp.asarray([0.2, -0.1], dtype=jnp.float32)[
        :, np.newaxis, np.newaxis
    ]
    constant_pv_aux_state = _replace_aux_state(
        aux_state,
        vorticity=(
            constant_layer_pv * layer_mass - equation.anticipated_pv_coriolis_parameter
        ),
    )

    flux_u, flux_v, _, diagnostics_valid = equation._anticipated_pv_flux_components(
        state,
        constant_pv_aux_state,
    )

    assert bool(diagnostics_valid)
    np.testing.assert_allclose(flux_u, 0.0, atol=1e-6)
    np.testing.assert_allclose(flux_v, 0.0, atol=1e-6)

    zero_wind_aux_state = _replace_aux_state(
        aux_state,
        cos_lat_u=(
            jnp.zeros_like(aux_state.cos_lat_u[0]),
            jnp.zeros_like(aux_state.cos_lat_u[1]),
        ),
    )
    candidate_tendencies = equation.curl_and_div_tendencies(
        zero_wind_aux_state,
        state=state,
    )
    incumbent_tendencies = incumbent_equation.curl_and_div_tendencies(
        zero_wind_aux_state,
        state=state,
    )
    _assert_tree_array_equal(candidate_tendencies, incumbent_tendencies)


@pytest.mark.parametrize(
    "invalid_diagnostic",
    ["nonpositive_mass", "nonfinite_coriolis", "nonfinite_step", "invalid_shape"],
)
def test_invalid_apvm_diagnostic_selects_exact_incumbent_pair(invalid_diagnostic):
    """Any invalid APVM diagnostic selects the complete incumbent pair."""
    coords, _, state, incumbent_equation, equation = _apvm_test_setup()
    aux_state = primitive_equations.compute_diagnostic_state_sigma(state, coords)
    candidate_state = state
    candidate_equation = equation
    if invalid_diagnostic == "nonpositive_mass":
        candidate_state = primitive_equations.State(
            vorticity=state.vorticity,
            divergence=state.divergence,
            temperature_variation=state.temperature_variation,
            log_surface_pressure=jnp.full_like(
                state.log_surface_pressure,
                -jnp.inf,
            ),
            tracers=state.tracers,
            sim_time=state.sim_time,
        )
    elif invalid_diagnostic == "nonfinite_coriolis":
        candidate_equation = replace(
            equation,
            anticipated_pv_coriolis_parameter=jnp.full(
                coords.horizontal.nodal_shape,
                jnp.nan,
                dtype=jnp.float32,
            ),
        )
    elif invalid_diagnostic == "nonfinite_step":
        candidate_equation = replace(
            equation,
            anticipated_pv_step_seconds=jnp.nan,
        )
    else:
        candidate_equation = replace(
            equation,
            anticipated_pv_coriolis_parameter=jnp.zeros((1,), dtype=jnp.float32),
        )

    candidate_tendencies = candidate_equation.curl_and_div_tendencies(
        aux_state,
        state=candidate_state,
    )
    incumbent_tendencies = incumbent_equation.curl_and_div_tendencies(
        aux_state,
        state=state,
    )

    _assert_tree_array_equal(candidate_tendencies, incumbent_tendencies)


def test_apvm_only_changes_momentum_tendencies_and_jits_finitely():
    """APVM changes only finite, clipped momentum tendencies under JIT."""
    coords, _, state, incumbent_equation, candidate_equation = _apvm_test_setup()
    selector_off_equation = replace(
        candidate_equation,
        use_anticipated_pv_flux=False,
    )

    incumbent_tendency = incumbent_equation.explicit_terms(state)
    selector_off_tendency = selector_off_equation.explicit_terms(state)
    candidate_tendency = candidate_equation.explicit_terms(state)
    jitted_candidate_tendency = jax.jit(candidate_equation.explicit_terms)(state)

    _assert_tree_array_equal(selector_off_tendency, incumbent_tendency)
    np.testing.assert_array_equal(
        candidate_tendency.temperature_variation,
        incumbent_tendency.temperature_variation,
    )
    np.testing.assert_array_equal(
        candidate_tendency.log_surface_pressure,
        incumbent_tendency.log_surface_pressure,
    )
    _assert_tree_array_equal(candidate_tendency.tracers, incumbent_tendency.tracers)
    assert not np.array_equal(
        candidate_tendency.vorticity,
        incumbent_tendency.vorticity,
    )
    assert not np.array_equal(
        candidate_tendency.divergence,
        incumbent_tendency.divergence,
    )
    for leaf in jax.tree_util.tree_leaves(jitted_candidate_tendency):
        assert bool(jnp.all(jnp.isfinite(leaf)))
    clipped_candidate = coords.horizontal.clip_wavenumbers(jitted_candidate_tendency)
    _assert_tree_array_equal(jitted_candidate_tendency, clipped_candidate)


def test_apvm_adapter_routes_physical_f_to_rollout_and_disables_dfi(monkeypatch):
    """The adapter routes physical Coriolis to rollout and disables APVM in DFI."""
    coords, physics_specs, _, _, _ = _apvm_test_setup()
    primitive_calls = []
    dfi_equations = []
    real_primitive_equation = dinosaur_adapter._primitive_equation

    def capture_primitive_equation(*args, **kwargs):
        primitive_calls.append(kwargs)
        return real_primitive_equation(*args, **kwargs)

    def fake_digital_filter_initialization(
        equation,
        ode_solver,
        filters,
        time_span,
        cutoff_period,
        dt,
    ):
        del ode_solver, filters, time_span, cutoff_period, dt
        dfi_equations.append(equation)
        return lambda dinosaur_state: dinosaur_state

    monkeypatch.setattr(
        dinosaur_adapter,
        "_primitive_equation",
        capture_primitive_equation,
    )
    monkeypatch.setattr(
        time_integration,
        "digital_filter_initialization",
        fake_digital_filter_initialization,
    )
    model = DinosaurPrimitiveEquationsDycoreModel(
        apply_digital_filter_initialization=True,
        apply_exact_coriolis_rotation_split=True,
        apply_symmetric_exact_coriolis_rotation_split=True,
        apply_anticipated_pv_flux=True,
        apply_spectral_filter=False,
        include_vertical_advection=False,
        jit_forecast=False,
    )

    model._trajectory_function(
        coords=coords,
        physics_specs=physics_specs,
        reference_temperature=np.full(coords.vertical.layers, 250.0),
        inner_steps=1,
        output_count=1,
        use_humidity_in_dynamics=False,
    )

    assert len(primitive_calls) == 2
    rollout_call, dfi_call = primitive_calls
    assert rollout_call["physics_specs"].angular_velocity == 0.0
    assert rollout_call["use_anticipated_pv_flux"]
    np.testing.assert_allclose(
        rollout_call["anticipated_pv_coriolis_parameter"],
        2.0 * physics_specs.angular_velocity * coords.horizontal.nodal_mesh[1],
    )
    assert rollout_call["anticipated_pv_step_seconds"] == _nondimensionalize_seconds(
        physics_specs,
        900.0,
    )
    assert dfi_call["physics_specs"] is physics_specs
    assert not dfi_call["use_anticipated_pv_flux"]
    assert dfi_call["anticipated_pv_step_seconds"] == 0.0
    assert dfi_call["anticipated_pv_coriolis_parameter"] is None
    assert len(dfi_equations) == 1
    assert not dfi_equations[0].use_anticipated_pv_flux
    assert dfi_equations[0].anticipated_pv_step_seconds == 0.0

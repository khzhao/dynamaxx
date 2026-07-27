# Copyright 2026 dynamaxx

"""Normalized spherical-spectral objectives for hybrid forecasts."""

from collections.abc import Callable
from dataclasses import dataclass

import jax
import jax.numpy as jnp
import numpy as np


@dataclass(frozen=True)
class SpectralLossStatistics:
    """Training-split normalizers for spectral state and power losses."""

    coefficient_variance: jax.Array
    climatological_power: jax.Array
    channel_weights: jax.Array

    def __post_init__(self):
        coefficient_variance = jnp.asarray(
            self.coefficient_variance,
            dtype=jnp.float32,
        )
        climatological_power = jnp.asarray(
            self.climatological_power,
            dtype=jnp.float32,
        )
        channel_weights = jnp.asarray(self.channel_weights, dtype=jnp.float32)
        if coefficient_variance.ndim != 2:
            raise ValueError("coefficient_variance must have shape (channel, l)")
        if climatological_power.shape != coefficient_variance.shape:
            raise ValueError("climatological_power must match coefficient_variance")
        if channel_weights.shape != (coefficient_variance.shape[0],):
            raise ValueError("channel_weights must have shape (channel,)")
        if not bool(jnp.all(jnp.isfinite(coefficient_variance))):
            raise ValueError("coefficient_variance must be finite")
        if not bool(jnp.all(jnp.isfinite(climatological_power))):
            raise ValueError("climatological_power must be finite")
        if not bool(jnp.all(jnp.isfinite(channel_weights))):
            raise ValueError("channel_weights must be finite")
        if not bool(jnp.all(coefficient_variance >= 0.0)):
            raise ValueError("coefficient_variance must be nonnegative")
        if not bool(jnp.all(climatological_power >= 0.0)):
            raise ValueError("climatological_power must be nonnegative")
        if not bool(jnp.all(channel_weights >= 0.0)):
            raise ValueError("channel_weights must be nonnegative")
        if not bool(jnp.any(channel_weights > 0.0)):
            raise ValueError("at least one channel weight must be positive")
        object.__setattr__(self, "coefficient_variance", coefficient_variance)
        object.__setattr__(self, "climatological_power", climatological_power)
        object.__setattr__(self, "channel_weights", channel_weights)


def _power_by_total_wavenumber(
    modal_coefficients: jax.Array,
    total_wavenumber: jax.Array,
    modal_mask: jax.Array,
    wavenumber_count: int,
) -> jax.Array:
    """Sum squared real modal coefficients for each total wavenumber."""
    modal_power = jnp.square(modal_coefficients) * modal_mask
    wavenumber_selector = jax.nn.one_hot(
        total_wavenumber,
        wavenumber_count,
        dtype=modal_power.dtype,
    )
    return jnp.einsum(
        "...vml,mlk->...vk",
        modal_power,
        wavenumber_selector,
        precision=jax.lax.Precision.HIGH,
    )


def estimate_spectral_loss_statistics(
    target_values: jax.Array,
    *,
    to_modal: Callable[[jax.Array], jax.Array],
    total_wavenumber: jax.Array,
    modal_mask: jax.Array,
    channel_weights: jax.Array | None = None,
) -> SpectralLossStatistics:
    """Estimate loss normalizers from a representative training-split sample.

    Args:
        target_values: Training states shaped ``(sample, channel, lon, lat)``.
        to_modal: Dinosaur-compatible spherical harmonic transform.
        total_wavenumber: Integer total-wavenumber index for every modal entry.
        modal_mask: Boolean mask of represented spherical-harmonic modes.
        channel_weights: Optional nonnegative weights. Uniform weights are used
            when omitted.
    """
    target_values = jnp.asarray(target_values, dtype=jnp.float32)
    if target_values.ndim != 4 or target_values.shape[0] < 2:
        raise ValueError(
            "target_values must have shape (sample, channel, lon, lat) "
            "with at least two samples"
        )
    total_wavenumber = jnp.asarray(total_wavenumber, dtype=jnp.int32)
    modal_mask = jnp.asarray(modal_mask, dtype=jnp.float32)
    modal_coefficients = to_modal(target_values)
    if modal_coefficients.shape[-2:] != total_wavenumber.shape:
        raise ValueError("modal transform and total_wavenumber shapes disagree")
    wavenumber_count = int(np.asarray(total_wavenumber).max()) + 1
    modal_mean = jnp.mean(modal_coefficients, axis=0)
    centered_coefficients = modal_coefficients - modal_mean
    centered_power = _power_by_total_wavenumber(
        centered_coefficients,
        total_wavenumber,
        modal_mask,
        wavenumber_count,
    )
    mode_counts = jnp.maximum(
        jnp.sum(
            jax.nn.one_hot(
                total_wavenumber,
                wavenumber_count,
                dtype=jnp.float32,
            )
            * modal_mask[..., jnp.newaxis],
            axis=(-3, -2),
        ),
        1.0,
    )
    coefficient_variance = jnp.mean(centered_power, axis=0) / mode_counts
    climatological_power = jnp.mean(
        _power_by_total_wavenumber(
            modal_coefficients,
            total_wavenumber,
            modal_mask,
            wavenumber_count,
        ),
        axis=0,
    )
    if channel_weights is None:
        channel_weights = jnp.ones(
            (target_values.shape[1],),
            dtype=jnp.float32,
        )
    return SpectralLossStatistics(
        coefficient_variance=coefficient_variance,
        climatological_power=climatological_power,
        channel_weights=channel_weights,
    )


def lead_time_spectral_taper(
    total_wavenumber: jax.Array,
    *,
    lead_hours: int,
    maximum_wavenumber: int,
    full_resolution_hours: int = 24,
    final_retained_fraction: float = 0.25,
    taper_width_fraction: float = 0.15,
) -> jax.Array:
    """Return a smooth configurable high-wavenumber accuracy taper.

    The taper affects only coefficient-error accuracy. The separate spectrum
    loss continues to constrain power at every represented wavenumber.
    """
    if lead_hours < 0:
        raise ValueError("lead_hours must be nonnegative")
    if maximum_wavenumber < 0:
        raise ValueError("maximum_wavenumber must be nonnegative")
    if not 0.0 < final_retained_fraction <= 1.0:
        raise ValueError("final_retained_fraction must be in (0, 1]")
    if not 0.0 < taper_width_fraction <= 1.0:
        raise ValueError("taper_width_fraction must be in (0, 1]")
    total_wavenumber = jnp.asarray(total_wavenumber, dtype=jnp.float32)
    if lead_hours <= full_resolution_hours or maximum_wavenumber == 0:
        return jnp.ones_like(total_wavenumber)
    progress = np.clip(
        np.log2(lead_hours / full_resolution_hours)
        / np.log2(360 / full_resolution_hours),
        0.0,
        1.0,
    )
    retained_fraction = 1.0 - progress * (1.0 - final_retained_fraction)
    full_weight_until = maximum_wavenumber * retained_fraction
    taper_width = max(1.0, taper_width_fraction * maximum_wavenumber)
    taper_progress = jnp.clip(
        (total_wavenumber - full_weight_until) / taper_width,
        0.0,
        1.0,
    )
    return 0.5 * (1.0 + jnp.cos(jnp.pi * taper_progress))


@dataclass(frozen=True)
class HybridForecastLoss:
    """Three-term normalized objective evaluated at selected forecast leads."""

    to_modal: Callable[[jax.Array], jax.Array]
    total_wavenumber: jax.Array
    modal_mask: jax.Array
    statistics: SpectralLossStatistics
    spectral_weight: float = 0.1
    bias_weight: float = 0.1
    epsilon: float = 1.0e-6
    bias_axis_name: str | None = None
    full_resolution_hours: int = 24
    final_retained_fraction: float = 0.25
    taper_width_fraction: float = 0.15
    interface_channel_scale: jax.Array | None = None
    forecast_channel_scale: jax.Array | None = None
    to_nodal: Callable[[jax.Array], jax.Array] | None = None
    area_weights: jax.Array | None = None

    def __post_init__(self):
        total_wavenumber = jnp.asarray(self.total_wavenumber, dtype=jnp.int32)
        modal_mask = jnp.asarray(self.modal_mask, dtype=jnp.float32)
        if total_wavenumber.ndim != 2:
            raise ValueError("total_wavenumber must be two-dimensional")
        if modal_mask.shape != total_wavenumber.shape:
            raise ValueError("modal_mask must match total_wavenumber")
        if self.statistics.coefficient_variance.shape[1] <= int(
            np.asarray(total_wavenumber).max()
        ):
            raise ValueError("statistics do not cover every total wavenumber")
        if self.spectral_weight < 0.0 or self.bias_weight < 0.0:
            raise ValueError("loss weights must be nonnegative")
        if self.epsilon <= 0.0:
            raise ValueError("epsilon must be positive")
        if self.full_resolution_hours < 1:
            raise ValueError("full_resolution_hours must be positive")
        if not 0.0 < self.final_retained_fraction <= 1.0:
            raise ValueError("final_retained_fraction must be in (0, 1]")
        if not 0.0 < self.taper_width_fraction <= 1.0:
            raise ValueError("taper_width_fraction must be in (0, 1]")
        interface_channel_scale = self.interface_channel_scale
        forecast_channel_scale = self.forecast_channel_scale
        expected_shape = (self.statistics.coefficient_variance.shape[0],)
        for scale_name, scale in (
            ("interface_channel_scale", interface_channel_scale),
            ("forecast_channel_scale", forecast_channel_scale),
        ):
            if scale is None:
                continue
            scale = jnp.asarray(scale, dtype=jnp.float32)
            if scale.shape != expected_shape:
                raise ValueError(f"{scale_name} must have shape {expected_shape}")
            if not bool(jnp.all(jnp.isfinite(scale) & (scale > 0.0))):
                raise ValueError(f"{scale_name} must be positive and finite")
            if scale_name == "interface_channel_scale":
                interface_channel_scale = scale
            else:
                forecast_channel_scale = scale
        if interface_channel_scale is not None or forecast_channel_scale is not None:
            if self.to_nodal is None or self.area_weights is None:
                raise ValueError("physical losses require to_nodal and area_weights")
            area_weights = jnp.asarray(self.area_weights, dtype=jnp.float32)
            if area_weights.ndim != 2:
                raise ValueError("area_weights must be two-dimensional")
            if not bool(jnp.all(jnp.isfinite(area_weights) & (area_weights >= 0.0))):
                raise ValueError("area_weights must be nonnegative and finite")
            if not bool(jnp.any(area_weights > 0.0)):
                raise ValueError("at least one area weight must be positive")
        else:
            area_weights = None
        object.__setattr__(self, "total_wavenumber", total_wavenumber)
        object.__setattr__(self, "modal_mask", modal_mask)
        object.__setattr__(self, "interface_channel_scale", interface_channel_scale)
        object.__setattr__(self, "forecast_channel_scale", forecast_channel_scale)
        object.__setattr__(self, "area_weights", area_weights)

    def _one_lead(
        self,
        forecast: jax.Array,
        target: jax.Array,
        lead_hours: int,
        bias_reference: jax.Array | None = None,
        *,
        target_is_modal: bool = False,
    ) -> tuple[jax.Array, jax.Array, jax.Array]:
        forecast_modal = self.to_modal(forecast)
        target_modal = target if target_is_modal else self.to_modal(target)
        modal_error = forecast_modal - target_modal
        channel_scale = (
            self.interface_channel_scale
            if lead_hours == 0
            else self.forecast_channel_scale
        )
        physical_state_loss = None
        physical_bias_loss = None
        if channel_scale is not None:
            if self.area_weights.shape != forecast.shape[-2:]:
                raise ValueError("area_weights must match the nodal spatial shape")
            target_nodal = self.to_nodal(target_modal) if target_is_modal else target
            normalized_area_weights = self.area_weights / jnp.sum(self.area_weights)
            normalized_error = (forecast - target_nodal) / channel_scale[
                :, jnp.newaxis, jnp.newaxis
            ]
            per_channel_error = jnp.sum(
                jnp.square(normalized_error) * normalized_area_weights,
                axis=(-2, -1),
            )
            physical_state_loss = jnp.sum(
                self.statistics.channel_weights * per_channel_error
            ) / jnp.maximum(
                jnp.sum(self.statistics.channel_weights),
                self.epsilon,
            )
            per_channel_bias = jnp.sum(
                normalized_error * normalized_area_weights,
                axis=(-2, -1),
            )
            if self.bias_axis_name is not None:
                per_channel_bias = jax.lax.pmean(
                    per_channel_bias,
                    axis_name=self.bias_axis_name,
                )
            physical_bias_loss = jnp.sum(
                self.statistics.channel_weights * jnp.square(per_channel_bias)
            ) / jnp.maximum(
                jnp.sum(self.statistics.channel_weights),
                self.epsilon,
            )
        if lead_hours == 0 and physical_state_loss is not None:
            zero = jnp.asarray(0.0, dtype=jnp.float32)
            return physical_state_loss, zero, zero
        maximum_wavenumber = self.statistics.coefficient_variance.shape[1] - 1
        taper = lead_time_spectral_taper(
            self.total_wavenumber,
            lead_hours=lead_hours,
            maximum_wavenumber=maximum_wavenumber,
            full_resolution_hours=self.full_resolution_hours,
            final_retained_fraction=self.final_retained_fraction,
            taper_width_fraction=self.taper_width_fraction,
        )
        variance_by_mode = jnp.take(
            self.statistics.coefficient_variance,
            self.total_wavenumber,
            axis=1,
        )
        channel_weights = self.statistics.channel_weights[:, jnp.newaxis, jnp.newaxis]
        if physical_state_loss is None:
            state_numerator = (
                channel_weights
                * taper
                * self.modal_mask
                * jnp.square(modal_error)
                / (variance_by_mode + self.epsilon)
            )
            state_denominator = jnp.maximum(
                jnp.sum(channel_weights * taper * self.modal_mask),
                self.epsilon,
            )
            state_loss = jnp.sum(state_numerator) / state_denominator
        else:
            state_loss = physical_state_loss

        wavenumber_count = self.statistics.climatological_power.shape[1]
        forecast_power = _power_by_total_wavenumber(
            forecast_modal,
            self.total_wavenumber,
            self.modal_mask,
            wavenumber_count,
        )
        target_power = _power_by_total_wavenumber(
            target_modal,
            self.total_wavenumber,
            self.modal_mask,
            wavenumber_count,
        )
        power_error = forecast_power - target_power
        power_normalizer = jnp.square(self.statistics.climatological_power)
        spectrum_loss = jnp.sum(
            self.statistics.channel_weights[:, jnp.newaxis]
            * jnp.square(power_error)
            / (power_normalizer + self.epsilon)
        ) / jnp.maximum(
            jnp.sum(self.statistics.channel_weights) * wavenumber_count,
            self.epsilon,
        )

        if physical_bias_loss is None:
            mean_modal_error = modal_error
            if bias_reference is not None:
                mean_modal_error = jax.lax.stop_gradient(bias_reference)
            elif self.bias_axis_name is not None:
                mean_modal_error = jax.lax.pmean(
                    mean_modal_error,
                    axis_name=self.bias_axis_name,
                )
            bias_numerator = jnp.sum(
                channel_weights
                * self.modal_mask
                * jnp.square(mean_modal_error)
                / (variance_by_mode + self.epsilon)
            )
            if bias_reference is not None:
                bias_numerator += 2.0 * jnp.sum(
                    channel_weights
                    * self.modal_mask
                    * mean_modal_error
                    * (modal_error - jax.lax.stop_gradient(modal_error))
                    / (variance_by_mode + self.epsilon)
                )
            bias_loss = bias_numerator / jnp.maximum(
                jnp.sum(channel_weights * self.modal_mask),
                self.epsilon,
            )
        else:
            bias_loss = physical_bias_loss
        return state_loss, spectrum_loss, bias_loss

    def __call__(
        self,
        forecasts: jax.Array,
        targets: jax.Array,
        lead_hours: tuple[int, ...],
        bias_reference: jax.Array | None = None,
        *,
        targets_are_modal: bool = False,
        lead_weights: tuple[float, ...] | None = None,
    ) -> tuple[jax.Array, dict[str, jax.Array]]:
        """Return lead-weighted total loss and scalar components."""
        forecasts = jnp.asarray(forecasts, dtype=jnp.float32)
        targets = jnp.asarray(targets, dtype=jnp.float32)
        if not targets_are_modal and forecasts.shape != targets.shape:
            raise ValueError("forecasts and targets must have identical shapes")
        if forecasts.ndim != 4 or forecasts.shape[0] != len(lead_hours):
            raise ValueError("forecasts must have shape (lead, channel, lon, lat)")
        if lead_weights is None:
            lead_weights = tuple(1.0 / len(lead_hours) for _ in lead_hours)
        if len(lead_weights) != len(lead_hours):
            raise ValueError("lead_weights must match lead_hours")
        host_lead_weights = np.asarray(lead_weights, dtype=np.float32)
        if not bool(np.all(np.isfinite(host_lead_weights))):
            raise ValueError("lead_weights must be finite")
        if not bool(np.all(host_lead_weights >= 0.0)):
            raise ValueError("lead_weights must be nonnegative")
        weight_sum = float(np.sum(host_lead_weights))
        if weight_sum <= 0.0:
            raise ValueError("at least one lead weight must be positive")
        normalized_lead_weights = jnp.asarray(
            host_lead_weights / weight_sum,
            dtype=jnp.float32,
        )
        expected_modal_shape = (
            forecasts.shape[0],
            forecasts.shape[1],
            *self.total_wavenumber.shape,
        )
        if targets_are_modal and targets.shape != expected_modal_shape:
            raise ValueError(
                "modal targets must have shape (lead, channel, modal_m, modal_l)"
            )
        components = []
        for index, lead in enumerate(lead_hours):
            lead_bias_reference = (
                None if bias_reference is None else bias_reference[index]
            )
            components.append(
                self._one_lead(
                    forecasts[index],
                    targets[index],
                    int(lead),
                    lead_bias_reference,
                    target_is_modal=targets_are_modal,
                )
            )
        state_loss = jnp.sum(
            normalized_lead_weights * jnp.stack([value[0] for value in components])
        )
        spectrum_loss = jnp.sum(
            normalized_lead_weights * jnp.stack([value[1] for value in components])
        )
        bias_loss = jnp.sum(
            normalized_lead_weights * jnp.stack([value[2] for value in components])
        )
        total_loss = (
            state_loss
            + self.spectral_weight * spectrum_loss
            + self.bias_weight * bias_loss
        )
        metrics = {
            "loss": total_loss,
            "loss/state": state_loss,
            "loss/spectrum": spectrum_loss,
            "loss/bias": bias_loss,
        }
        for lead_hours_value, (lead_state, lead_spectrum, lead_bias) in zip(
            lead_hours,
            components,
            strict=True,
        ):
            lead_prefix = f"loss/{lead_hours_value}h"
            metrics[f"{lead_prefix}/state"] = lead_state
            metrics[f"{lead_prefix}/spectrum"] = lead_spectrum
            metrics[f"{lead_prefix}/bias"] = lead_bias
        return total_loss, metrics

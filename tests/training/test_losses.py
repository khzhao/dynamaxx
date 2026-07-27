# Copyright 2026 dynamaxx

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.training.losses import (
    HybridForecastLoss,
    SpectralLossStatistics,
    estimate_spectral_loss_statistics,
    lead_time_spectral_taper,
)


def _loss():
    total_wavenumber = jnp.asarray([[0, 1], [1, 1]])
    modal_mask = jnp.ones((2, 2))
    statistics = SpectralLossStatistics(
        coefficient_variance=jnp.ones((1, 2)),
        climatological_power=jnp.ones((1, 2)),
        channel_weights=jnp.ones((1,)),
    )
    return HybridForecastLoss(
        to_modal=lambda values: values,
        total_wavenumber=total_wavenumber,
        modal_mask=modal_mask,
        statistics=statistics,
        spectral_weight=0.1,
        bias_weight=0.1,
    )


def test_exact_forecast_has_zero_three_term_loss():
    """A perfect forecast must have zero state, spectrum, and bias loss."""
    values = jnp.arange(8, dtype=jnp.float32).reshape(2, 1, 2, 2)

    total, metrics = _loss()(values, values, (6, 12))

    np.testing.assert_allclose(total, 0.0)
    np.testing.assert_allclose(metrics["loss/state"], 0.0)
    np.testing.assert_allclose(metrics["loss/spectrum"], 0.0)
    np.testing.assert_allclose(metrics["loss/bias"], 0.0)


def test_forecast_error_contributes_to_every_loss_term():
    """A uniform forecast error must activate all objective components."""
    targets = jnp.ones((1, 1, 2, 2))
    forecasts = 1.5 * targets

    total, metrics = _loss()(forecasts, targets, (6,))

    assert float(total) > 0.0
    assert float(metrics["loss/state"]) > 0.0
    assert float(metrics["loss/spectrum"]) > 0.0
    assert float(metrics["loss/bias"]) > 0.0


def test_explicit_lead_weights_emphasize_the_selected_error():
    """Lead weighting must change aggregate loss without changing components."""
    targets = jnp.zeros((2, 1, 2, 2))
    forecasts = targets.at[0].set(1.0).at[1].set(3.0)
    loss = _loss()

    early_total, _ = loss(
        forecasts,
        targets,
        (0, 6),
        lead_weights=(0.9, 0.1),
    )
    late_total, _ = loss(
        forecasts,
        targets,
        (0, 6),
        lead_weights=(0.1, 0.9),
    )

    assert float(late_total) > float(early_total)


def test_lead_zero_uses_interface_reconstruction_scale():
    """Lead-zero loss weights physical reconstruction errors per channel."""
    loss = HybridForecastLoss(
        to_modal=lambda values: values,
        total_wavenumber=jnp.zeros((1, 1), dtype=jnp.int32),
        modal_mask=jnp.ones((1, 1), dtype=jnp.float32),
        statistics=SpectralLossStatistics(
            coefficient_variance=jnp.ones((2, 1), dtype=jnp.float32),
            climatological_power=jnp.ones((2, 1), dtype=jnp.float32),
            channel_weights=jnp.ones((2,), dtype=jnp.float32),
        ),
        interface_channel_scale=jnp.asarray([2.0, 4.0]),
        to_nodal=lambda values: values,
        area_weights=jnp.ones((1, 1), dtype=jnp.float32),
    )
    forecasts = jnp.asarray([[[[2.0]], [[4.0]]]])
    targets = jnp.zeros_like(forecasts)

    value, metrics = loss(forecasts, targets, (0,))

    np.testing.assert_allclose(value, 1.0)
    np.testing.assert_allclose(metrics["loss/0h/state"], 1.0)
    np.testing.assert_allclose(metrics["loss/0h/spectrum"], 0.0)
    np.testing.assert_allclose(metrics["loss/0h/bias"], 0.0)


def test_positive_lead_uses_temporal_difference_scale():
    """Forecast state and bias terms track normalized physical errors."""
    loss = HybridForecastLoss(
        to_modal=lambda values: values,
        total_wavenumber=jnp.zeros((1, 1), dtype=jnp.int32),
        modal_mask=jnp.ones((1, 1), dtype=jnp.float32),
        statistics=SpectralLossStatistics(
            coefficient_variance=100.0 * jnp.ones((2, 1), dtype=jnp.float32),
            climatological_power=jnp.ones((2, 1), dtype=jnp.float32),
            channel_weights=jnp.ones((2,), dtype=jnp.float32),
        ),
        forecast_channel_scale=jnp.asarray([2.0, 4.0]),
        to_nodal=lambda values: values,
        area_weights=jnp.ones((1, 1), dtype=jnp.float32),
    )
    forecasts = jnp.asarray([[[[2.0]], [[4.0]]]])
    targets = jnp.zeros_like(forecasts)

    _, metrics = loss(forecasts, targets, (6,))

    np.testing.assert_allclose(metrics["loss/6h/state"], 1.0)
    np.testing.assert_allclose(metrics["loss/6h/bias"], 1.0)


def test_precomputed_modal_targets_match_nodal_target_loss_and_gradient():
    """Cached modal targets must preserve objective values and gradients."""
    targets = jnp.ones((1, 1, 2, 2))
    loss = _loss()

    nodal_value, nodal_gradient = jax.value_and_grad(
        lambda forecasts: loss(forecasts, targets, (6,))[0]
    )(1.5 * targets)
    modal_value, modal_gradient = jax.value_and_grad(
        lambda forecasts: loss(
            forecasts,
            targets,
            (6,),
            targets_are_modal=True,
        )[0]
    )(1.5 * targets)

    np.testing.assert_allclose(modal_value, nodal_value)
    np.testing.assert_allclose(modal_gradient, nodal_gradient)


def test_statistics_are_estimated_by_channel_and_total_wavenumber():
    """Spectral normalizers must retain channel and wavenumber structure."""
    targets = jnp.asarray(
        [
            [[[1.0, 2.0], [3.0, 4.0]]],
            [[[2.0, 4.0], [6.0, 8.0]]],
        ]
    )
    statistics = estimate_spectral_loss_statistics(
        targets,
        to_modal=lambda values: values,
        total_wavenumber=jnp.asarray([[0, 1], [1, 1]]),
        modal_mask=jnp.ones((2, 2)),
    )

    assert statistics.coefficient_variance.shape == (1, 2)
    assert statistics.climatological_power.shape == (1, 2)
    assert bool(jnp.all(statistics.coefficient_variance > 0.0))


def test_taper_preserves_short_leads_and_reduces_long_lead_high_modes():
    """Lead tapering must preserve short-range detail and relax long leads."""
    total_wavenumber = jnp.arange(9)

    short_taper = lead_time_spectral_taper(
        total_wavenumber,
        lead_hours=24,
        maximum_wavenumber=8,
    )
    long_taper = lead_time_spectral_taper(
        total_wavenumber,
        lead_hours=360,
        maximum_wavenumber=8,
    )

    np.testing.assert_array_equal(short_taper, jnp.ones_like(short_taper))
    assert float(long_taper[0]) == 1.0
    assert float(long_taper[-1]) == 0.0


def test_fixed_global_bias_reference_has_exact_batch_mean_gradient():
    """A fixed global mean error must reproduce the exact bias gradient."""
    loss = HybridForecastLoss(
        to_modal=lambda values: values,
        total_wavenumber=jnp.zeros((1, 1), dtype=jnp.int32),
        modal_mask=jnp.ones((1, 1)),
        statistics=SpectralLossStatistics(
            coefficient_variance=jnp.ones((1, 1)),
            climatological_power=jnp.ones((1, 1)),
            channel_weights=jnp.ones((1,)),
        ),
    )
    target = jnp.zeros((1, 1, 1))
    global_mean_error = jnp.full((1, 1, 1), 2.0)

    bias_value, bias_gradient = jax.value_and_grad(
        lambda forecast_value: loss._one_lead(
            jnp.full((1, 1, 1), forecast_value),
            target,
            6,
            global_mean_error,
        )[2]
    )(jnp.asarray(1.0))

    np.testing.assert_allclose(bias_value, 4.0, rtol=1.0e-5)
    np.testing.assert_allclose(bias_gradient, 4.0, rtol=1.0e-5)

# Copyright 2026 dynamaxx

import jax.numpy as jnp
import numpy as np

from dynamaxx.eval.core import WeatherVariable
from dynamaxx.eval.metrics import (
    area_weighted_mean,
    merge_totals,
    score_totals,
    totals_to_records,
)


def test_area_weighted_mean_averages_last_two_axes():
    """Area-weighted mean should reduce longitude-latitude axes."""
    values = jnp.asarray([[[1.0, 3.0], [5.0, 7.0]]])
    weights = jnp.asarray([[1.0, 1.0], [1.0, 3.0]])

    mean = area_weighted_mean(values, weights)

    np.testing.assert_allclose(mean, np.array([5.0]))


def test_metric_totals_merge_squared_errors_before_rmse():
    """Metric totals should merge squared errors before taking RMSE."""
    truth = jnp.zeros((1, 1, 1, 1, 1))
    variables = (WeatherVariable("2m_temperature"),)
    first = score_totals(
        jnp.ones_like(truth) * 2.0,
        truth,
        jnp.ones((1, 1)),
        model_name="candidate",
        variables=variables,
        lead_hours=(6,),
    )
    second = score_totals(
        jnp.ones_like(truth) * 4.0,
        truth,
        jnp.ones((1, 1)),
        model_name="candidate",
        variables=variables,
        lead_hours=(6,),
    )

    merged = merge_totals(first + second)
    records = totals_to_records(merged, merged)

    assert len(records) == 1
    np.testing.assert_allclose(records[0].rmse, np.sqrt((4.0 + 16.0) / 2.0))
    assert records[0].skill_vs_persistence is not None
    np.testing.assert_allclose(records[0].skill_vs_persistence, 0.0)
    assert records[0].structure_score is None


def test_structure_score_rewards_wave_phase_and_amplitude():
    """Structure score should be one for a perfect spatial anomaly forecast."""
    truth = jnp.asarray([[[[[-1.0], [1.0], [-1.0], [1.0]]]]])
    variables = (WeatherVariable("geopotential", level=500),)
    totals = score_totals(
        truth,
        truth,
        jnp.ones((4, 1)),
        model_name="candidate",
        variables=variables,
        lead_hours=(24,),
    )

    records = totals_to_records(totals, totals)

    record = records[0]
    assert record.spatial_anomaly_correlation is not None
    assert record.spatial_variance_ratio is not None
    assert record.structure_score is not None
    assert record.structure_skill_vs_persistence is not None
    assert record.zonal_eddy_correlation is not None
    assert record.zonal_eddy_variance_ratio is not None
    assert record.zonal_eddy_score is not None
    assert record.zonal_eddy_skill_vs_persistence is not None
    np.testing.assert_allclose(record.spatial_anomaly_correlation, 1.0)
    np.testing.assert_allclose(record.spatial_variance_ratio, 1.0)
    np.testing.assert_allclose(record.structure_score, 1.0)
    np.testing.assert_allclose(record.structure_skill_vs_persistence, 0.0)
    np.testing.assert_allclose(record.zonal_eddy_correlation, 1.0)
    np.testing.assert_allclose(record.zonal_eddy_variance_ratio, 1.0)
    np.testing.assert_allclose(record.zonal_eddy_score, 1.0)
    np.testing.assert_allclose(record.zonal_eddy_skill_vs_persistence, 0.0)


def test_structure_skill_penalizes_spatially_flat_forecast():
    """Structure skill should penalize collapsed spatial variance."""
    truth = jnp.asarray([[[[[-1.0], [1.0], [-1.0], [1.0]]]]])
    flat_forecast = jnp.zeros_like(truth)
    variables = (WeatherVariable("geopotential", level=500),)
    model_totals = score_totals(
        flat_forecast,
        truth,
        jnp.ones((4, 1)),
        model_name="candidate",
        variables=variables,
        lead_hours=(24,),
    )
    persistence_totals = score_totals(
        truth,
        truth,
        jnp.ones((4, 1)),
        model_name="persistence",
        variables=variables,
        lead_hours=(24,),
    )

    records = totals_to_records(model_totals, persistence_totals)

    record = records[0]
    assert record.spatial_anomaly_correlation is not None
    assert record.spatial_variance_ratio is not None
    assert record.structure_score is not None
    assert record.structure_skill_vs_persistence is not None
    assert record.zonal_eddy_correlation is not None
    assert record.zonal_eddy_variance_ratio is not None
    assert record.zonal_eddy_score is not None
    assert record.zonal_eddy_skill_vs_persistence is not None
    np.testing.assert_allclose(record.spatial_anomaly_correlation, 0.0)
    np.testing.assert_allclose(record.spatial_variance_ratio, 0.0)
    np.testing.assert_allclose(record.structure_score, 0.0)
    np.testing.assert_allclose(record.structure_skill_vs_persistence, -1.0)
    np.testing.assert_allclose(record.zonal_eddy_correlation, 0.0)
    np.testing.assert_allclose(record.zonal_eddy_variance_ratio, 0.0)
    np.testing.assert_allclose(record.zonal_eddy_score, 0.0)
    np.testing.assert_allclose(record.zonal_eddy_skill_vs_persistence, -1.0)


def test_zonal_eddy_score_penalizes_latitude_band_forecast():
    """Zonal-eddy score should catch latitude bands without longitude structure."""
    longitude_wave = jnp.asarray([-1.0, 1.0, -1.0, 1.0])[:, jnp.newaxis]
    latitude_band = jnp.asarray([[0.0, 2.0]])
    truth = (latitude_band + longitude_wave)[jnp.newaxis, jnp.newaxis, jnp.newaxis]
    forecast = jnp.broadcast_to(
        latitude_band,
        (1, 1, 1, 4, 2),
    )
    variables = (WeatherVariable("mean_sea_level_pressure"),)
    model_totals = score_totals(
        forecast,
        truth,
        jnp.ones((4, 2)),
        model_name="candidate",
        variables=variables,
        lead_hours=(24,),
    )
    persistence_totals = score_totals(
        truth,
        truth,
        jnp.ones((4, 2)),
        model_name="persistence",
        variables=variables,
        lead_hours=(24,),
    )

    record = totals_to_records(model_totals, persistence_totals)[0]

    assert record.structure_score is not None
    assert record.zonal_eddy_score is not None
    assert record.zonal_eddy_skill_vs_persistence is not None
    assert record.structure_score > 0.0
    np.testing.assert_allclose(record.zonal_eddy_score, 0.0)
    np.testing.assert_allclose(record.zonal_eddy_skill_vs_persistence, -1.0)

# Copyright 2026 dynamaxx

"""Normalization statistics for corrector features and loss weights.

The processed dataset ships per-year, per-gridpoint temporal moments in
`stats/<year>.zarr` (variables `mean`, `std`, `sample_count`; reduction over
time). We pool them across training years and reduce over space to get one
scalar (mean, std) per channel.

Everything here is host-side NumPy/xarray: statistics are computed once and
baked into the training configuration, never traced by JAX.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import xarray as xr

LOG_SURFACE_PRESSURE_MEAN = 0.0
LOG_SURFACE_PRESSURE_STD = 0.05


def pool_yearly_moments(
    means: np.ndarray,
    stds: np.ndarray,
    counts: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Pool per-year (mean, std, count) into overall (mean, std).

    Uses the exact two-moment identity: with per-year sample counts n_i,
    means m_i and (population, ddof=0) stds s_i,

        m  = sum(n_i m_i) / N
        E2 = sum(n_i (s_i^2 + m_i^2)) / N
        var = E2 - m^2

    Args:
      means: `[year, ...]` per-year means.
      stds: `[year, ...]` per-year population stds (matches `std_ddof: 0`
        in the dataset attributes).
      counts: `[year]` per-year sample counts.

    Returns:
      Pooled (mean, std) with shape `[...]`, float64.
    """
    means = np.asarray(means, np.float64)
    stds = np.asarray(stds, np.float64)
    counts = np.asarray(counts, np.float64)
    assert counts.shape[0] == means.shape[0] == stds.shape[0]
    weights = counts.reshape((-1,) + (1,) * (means.ndim - 1))
    total = weights.sum(axis=0)
    mean = (weights * means).sum(axis=0) / total
    second_moment = (weights * (stds**2 + means**2)).sum(axis=0) / total
    variance = np.maximum(second_moment - mean**2, 0.0)
    return mean, np.sqrt(variance)


def cos_latitude_weights(latitude_deg: np.ndarray) -> np.ndarray:
    """Normalized cos-latitude area weights for a latitude vector."""
    weights = np.maximum(np.cos(np.deg2rad(np.asarray(latitude_deg))), 0.0)
    return weights / weights.sum()


def spatial_scalar_stats(
    mean_map: np.ndarray,
    std_map: np.ndarray,
    latitude_deg: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Reduce per-gridpoint (mean, std) maps to per-channel scalars.

    The scalar mean is the area-weighted mean of the mean map. The scalar
    std is the sqrt of the area-weighted TOTAL second central moment: the
    temporal variance plus the spatial variance of the temporal mean. This
    is the std of the channel over (time, space) jointly, which is the right
    scale for feature normalization: a feature like T at 1000 hPa varies far
    more in space (pole vs tropics) than in time at one point.

    Args:
      mean_map: `[channel, lon, lat]` pooled temporal means.
      std_map: `[channel, lon, lat]` pooled temporal stds.
      latitude_deg: `[lat]` latitudes in degrees.

    Returns:
      (mean, std) arrays of shape `[channel]`, float64.
    """
    weights = cos_latitude_weights(latitude_deg)[None, None, :]
    lon_count = mean_map.shape[1]
    weights = np.broadcast_to(weights / lon_count, mean_map.shape)
    scalar_mean = (weights * mean_map).sum(axis=(1, 2))
    total_second = (weights * (std_map**2 + mean_map**2)).sum(axis=(1, 2))
    variance = np.maximum(total_second - scalar_mean**2, 0.0)
    return scalar_mean, np.sqrt(variance)


def pooled_channel_stats(
    dataset_path: str,
    years: Sequence[int],
) -> tuple[tuple[str, ...], np.ndarray, np.ndarray]:
    """Load stats/<year>.zarr for `years` and return per-channel scalars.

    Returns:
      (channel_names, mean[channel], std[channel]).
    """
    means, stds, counts = [], [], []
    channels: tuple[str, ...] | None = None
    latitude = None
    for year in years:
        ds = xr.open_zarr(
            f"{dataset_path.rstrip('/')}/stats/{int(year)}.zarr",
            consolidated=None,
        )
        year_channels = tuple(str(c) for c in ds["channel"].values)
        if channels is None:
            channels = year_channels
            latitude = np.asarray(ds["latitude"].values, np.float64)
        else:
            assert year_channels == channels, f"channel mismatch in {year}"
        means.append(ds["mean"].values[0])
        stds.append(ds["std"].values[0])
        counts.append(int(ds["sample_count"].values[0]))
    assert channels is not None and latitude is not None
    mean_map, std_map = pool_yearly_moments(
        np.stack(means), np.stack(stds), np.asarray(counts)
    )
    scalar_mean, scalar_std = spatial_scalar_stats(mean_map, std_map, latitude)
    return channels, scalar_mean, scalar_std


def feature_stats_from_channels(
    channel_names: Sequence[str],
    channel_mean: np.ndarray,
    channel_std: np.ndarray,
    pressure_levels_hpa: Sequence[int],
) -> tuple[np.ndarray, np.ndarray]:
    """Build the (3L + 1) state-feature mean/std vectors from channel stats.

    Feature order matches `features.assemble_features`: temperature at each
    of the L pressure levels (top to bottom, dataset order), then u, then v,
    then log(ps / 1e5 Pa).

    Approximation, stated explicitly: sigma layer k is normalized with the
    stats of the k-th PRESSURE level. Sigma and pressure levels only roughly
    coincide (they match best away from terrain), but for normalization —
    where only the ORDER OF MAGNITUDE matters — this is fine. Do not reuse
    these vectors as physical climatologies.

    Returns:
      (mean, std) float32 vectors of length 3 * L + 1.
    """
    index = {name: i for i, name in enumerate(channel_names)}
    blocks_mean: list[np.ndarray] = []
    blocks_std: list[np.ndarray] = []
    for variable in ("temperature", "u_component_of_wind", "v_component_of_wind"):
        rows = [index[f"{variable}_{level}"] for level in pressure_levels_hpa]
        blocks_mean.append(np.asarray(channel_mean)[rows])
        blocks_std.append(np.asarray(channel_std)[rows])
    mean = np.concatenate(blocks_mean + [[LOG_SURFACE_PRESSURE_MEAN]])
    std = np.concatenate(blocks_std + [[LOG_SURFACE_PRESSURE_STD]])
    assert np.all(std > 0.0)
    return mean.astype(np.float32), std.astype(np.float32)

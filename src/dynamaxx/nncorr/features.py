# Copyright 2026 dynamaxx

"""Corrector input features: per-column state plus static embeddings.

Column-locality is the load-bearing inductive bias, inherited from
NeuralGCM: the network sees ONE atmospheric column at a time (all L layers
of T, u, v, plus surface pressure and static surface descriptors) and emits
corrections for THAT column. Horizontal structure is left entirely to the
resolved spectral dynamics. This is why a plain MLP is enough, why the
parameter count is independent of resolution, and why the same weights
apply at every grid point (the ultimate weight sharing).
"""

from __future__ import annotations

import dataclasses

import jax
import jax.numpy as jnp
import numpy as np

STATIC_FEATURE_NAMES: tuple[str, ...] = (
    "sin_latitude",
    "cos_latitude",
    "sin_longitude",
    "cos_longitude",
    "orography_normalized",
    "land_fraction",
)

OROGRAPHY_SCALE_METERS = 3000.0
REFERENCE_SURFACE_PRESSURE_PA = 1.0e5


@dataclasses.dataclass(frozen=True)
class FeatureSpec:
    """Shapes contract between features, MLP, and corrector."""

    layer_count: int
    static_count: int = len(STATIC_FEATURE_NAMES)

    @property
    def state_dim(self) -> int:
        """T, u, v at each layer plus log surface pressure."""
        return 3 * self.layer_count + 1

    @property
    def feature_dim(self) -> int:
        return self.state_dim + self.static_count

    @property
    def output_dim(self) -> int:
        """dT, du, dv tendencies at each layer."""
        return 3 * self.layer_count


def static_features(
    longitude_deg: np.ndarray,
    latitude_deg: np.ndarray,
    *,
    orography_m: np.ndarray | None = None,
    land_fraction: np.ndarray | None = None,
) -> jax.Array:
    """Build the `[len(STATIC_FEATURE_NAMES), lon, lat]` static feature stack.

    The trig embeddings give the column its location without a coordinate
    discontinuity; orography is normalized by a fixed 3000 m scale; land
    fraction is already in [0, 1]. Missing surface fields become zeros so
    fully synthetic tests need no data on disk.

    IMPORTANT orientation note: `longitude_deg`/`latitude_deg` (and the
    optional maps) must be in DINOSAUR grid order, i.e. the order of
    `coords.horizontal` nodal arrays. If you load surface fields from the
    dataset with the adapter helpers, convert them with
    `adapter._to_dinosaur_latitude_order(field, latitude_reversed)` first —
    a silently flipped latitude axis is the classic bug in this codebase
    family, and nothing will crash to warn you.
    """
    longitude_rad = np.deg2rad(np.asarray(longitude_deg, np.float64))
    latitude_rad = np.deg2rad(np.asarray(latitude_deg, np.float64))
    lon_mesh, lat_mesh = np.meshgrid(longitude_rad, latitude_rad, indexing="ij")
    spatial_shape = lon_mesh.shape

    def _or_zeros(field: np.ndarray | None, scale: float) -> np.ndarray:
        if field is None:
            return np.zeros(spatial_shape)
        field = np.asarray(field, np.float64)
        assert field.shape == spatial_shape, (
            f"surface field shape {field.shape} != grid {spatial_shape}"
        )
        return field / scale

    stack = np.stack(
        [
            np.sin(lat_mesh),
            np.cos(lat_mesh),
            np.sin(lon_mesh),
            np.cos(lon_mesh),
            _or_zeros(orography_m, OROGRAPHY_SCALE_METERS),
            _or_zeros(land_fraction, 1.0),
        ]
    )
    return jnp.asarray(stack, dtype=jnp.float32)


def load_static_surface_fields(
    longitude: np.ndarray,
    latitude: np.ndarray,
    initial_time: np.datetime64,
    latitude_reversed: bool,
) -> dict[str, np.ndarray | None]:
    """Load orography and land fraction on the dinosaur grid, or None.

    Reuses the adapter's cached, grid-validated loaders (private functions;
    acceptable inside this tutorial branch). Either value may be None when
    the dataset cannot serve the exact grid — callers fall back to zeros,
    which reproduces the graceful-degradation idiom used by every accepted
    feature.
    """
    from dynamaxx.dycore.models.dinosaur import adapter

    orography = adapter._load_surface_geopotential_height_for_grid(
        longitude=longitude, latitude=latitude, initial_time=initial_time
    )
    land = adapter._load_land_sea_fraction_for_grid(
        longitude=longitude, latitude=latitude, initial_time=initial_time
    )
    if orography is not None:
        orography = np.asarray(
            adapter._to_dinosaur_latitude_order(orography, latitude_reversed)
        )
    if land is not None:
        land = np.asarray(
            adapter._to_dinosaur_latitude_order(land, latitude_reversed)
        )
    return {"orography_m": orography, "land_fraction": land}


def assemble_features(
    fields_si: dict[str, jax.Array],
    static_stack: jax.Array,
    state_mean: jax.Array,
    state_std: jax.Array,
) -> jax.Array:
    """EXERCISE 2 — build the normalized `[lon, lat, F]` feature array.

    Inputs:
      * `fields_si`: from `corrector.decode_nodal_si`. Keys and shapes:
        "temperature" `[L, lon, lat]` (K), "u" and "v" `[L, lon, lat]`
        (m/s), "surface_pressure" `[lon, lat]` (Pa).
      * `static_stack`: `[S, lon, lat]` from `static_features` (already
        O(1); do not renormalize).
      * `state_mean`, `state_std`: `[3L + 1]` vectors from
        `normalize.feature_stats_from_channels`, ordered T-block, u-block,
        v-block, then log-pressure.

    Required output feature order along the last axis (the tests enforce
    it): T_1..T_L, u_1..u_L, v_1..v_L, log(ps / 1e5), then the six statics.
    State features are standardized as (x - mean) / std; the log-pressure
    feature is log(ps / REFERENCE_SURFACE_PRESSURE_PA) standardized with its
    entry in the vectors. Return float32 `[lon, lat, 3L + 1 + S]`.

    Implementation notes (think about WHY for each):
      * You want axis moves (`jnp.moveaxis`) and one `concatenate`, not
        Python loops over layers.
      * Cast to float32 at the END: the decode produced float32 already,
        but the standardization constants arrive as float32 vectors and
        broadcasting rules will not upcast silently (unlike some torch ops).
      * Everything here must remain traceable: no `.item()`, no NumPy calls
        on traced arrays (np.moveaxis on a traced array silently works via
        __array_function__? — it does NOT; it raises. Try it and read the
        error, it is educational).

    Acceptance test:
      uv run pytest tests/nncorr/test_exercises.py -k features -m exercise
    """
    raise NotImplementedError("EXERCISE 2: see tutorial/03-corrector-design.md")

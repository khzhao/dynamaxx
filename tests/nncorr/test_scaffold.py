# Copyright 2026 dynamaxx

"""Tests for the PROVIDED scaffold. These must pass before you start.

    JAX_PLATFORMS=cpu uv run pytest tests/nncorr -m "not exercise" -q
"""

import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.nncorr import checkpoint as ckpt_lib
from dynamaxx.nncorr import corrector, features, mlp, normalize, rollout


def test_checkpoint_roundtrip(tmp_path):
    tree = {
        "layers": [
            {"w": jnp.arange(6.0).reshape(2, 3), "b": jnp.zeros(3)},
            {"w": jnp.ones((3, 1)), "b": jnp.full(1, 2.0)},
        ],
        "scale": jnp.asarray(0.5),
    }
    path = str(tmp_path / "params.npz")
    ckpt_lib.save_pytree(path, tree)
    template = jax.tree_util.tree_map(jnp.zeros_like, tree)
    restored = ckpt_lib.load_pytree(path, template)
    for a, b in zip(
        jax.tree_util.tree_leaves(tree),
        jax.tree_util.tree_leaves(restored),
        strict=True,
    ):
        np.testing.assert_array_equal(np.asarray(a), np.asarray(b))


def test_pool_yearly_moments_matches_bruteforce():
    rng = np.random.default_rng(0)
    year_a = rng.normal(2.0, 3.0, size=(40, 5))
    year_b = rng.normal(-1.0, 0.5, size=(70, 5))
    means = np.stack([year_a.mean(0), year_b.mean(0)])
    stds = np.stack([year_a.std(0), year_b.std(0)])
    counts = np.array([40, 70])
    mean, std = normalize.pool_yearly_moments(means, stds, counts)
    combined = np.concatenate([year_a, year_b], axis=0)
    np.testing.assert_allclose(mean, combined.mean(0), rtol=1e-12)
    np.testing.assert_allclose(std, combined.std(0), rtol=1e-10)


def test_spatial_scalar_stats_total_variance():
    latitude = np.linspace(-90, 90, 9)
    mean_map = np.zeros((2, 4, 9))
    mean_map[1] = 10.0
    std_map = np.full((2, 4, 9), 2.0)
    mean, std = normalize.spatial_scalar_stats(mean_map, std_map, latitude)
    np.testing.assert_allclose(mean, [0.0, 10.0], atol=1e-12)
    # Spatially uniform mean: total std reduces to the temporal std.
    np.testing.assert_allclose(std, [2.0, 2.0], rtol=1e-12)


def test_feature_stats_from_channels_ordering():
    levels = (500, 900)
    channels = (
        "temperature_500",
        "temperature_900",
        "u_component_of_wind_500",
        "u_component_of_wind_900",
        "v_component_of_wind_500",
        "v_component_of_wind_900",
        "unrelated_channel",
    )
    channel_mean = np.arange(len(channels), dtype=np.float64)
    channel_std = np.arange(1, len(channels) + 1, dtype=np.float64)
    mean, std = normalize.feature_stats_from_channels(
        channels, channel_mean, channel_std, levels
    )
    assert mean.shape == std.shape == (2 * 3 + 1,)
    np.testing.assert_allclose(mean[:6], [0, 1, 2, 3, 4, 5])
    np.testing.assert_allclose(std[:6], [1, 2, 3, 4, 5, 6])
    assert mean[6] == normalize.LOG_SURFACE_PRESSURE_MEAN
    assert std[6] == normalize.LOG_SURFACE_PRESSURE_STD


def test_static_features_shapes_and_ranges():
    longitude = np.arange(8) * 45.0
    latitude = np.linspace(-90, 90, 5)
    stack = features.static_features(longitude, latitude)
    assert stack.shape == (len(features.STATIC_FEATURE_NAMES), 8, 5)
    assert bool(jnp.all(jnp.isfinite(stack)))
    # sin(lat) runs -1 -> 1 along the latitude axis at every longitude.
    np.testing.assert_allclose(
        np.asarray(stack[0, 0]), np.sin(np.deg2rad(latitude)), atol=1e-6
    )
    # Missing surface fields are exactly zero.
    np.testing.assert_array_equal(np.asarray(stack[4]), 0.0)
    np.testing.assert_array_equal(np.asarray(stack[5]), 0.0)


def test_mlp_init_shapes_and_zero_final():
    params = mlp.init_mlp_params(jax.random.PRNGKey(0), 19, (32, 16), 12)
    assert [p["w"].shape for p in params] == [(19, 32), (32, 16), (16, 12)]
    assert [p["b"].shape for p in params] == [(32,), (16,), (12,)]
    np.testing.assert_array_equal(np.asarray(params[-1]["w"]), 0.0)
    np.testing.assert_array_equal(np.asarray(params[-1]["b"]), 0.0)
    assert mlp.parameter_count(params) == 19 * 32 + 32 + 32 * 16 + 16 + 16 * 12 + 12


def test_decode_nodal_si(tiny_bundle, tiny_state, tiny_shapes):
    fields = corrector.decode_nodal_si(
        tiny_state,
        coords=tiny_bundle.coords,
        physics_specs=tiny_bundle.physics_specs,
        reference_temperature=tiny_bundle.reference_temperature,
    )
    layer_count = tiny_bundle.layer_count
    assert fields["temperature"].shape == (layer_count, *tiny_shapes.nodal)
    assert fields["u"].shape == (layer_count, *tiny_shapes.nodal)
    assert fields["v"].shape == (layer_count, *tiny_shapes.nodal)
    assert fields["surface_pressure"].shape == tiny_shapes.nodal
    for value in fields.values():
        assert bool(jnp.all(jnp.isfinite(value)))
    # The rest state was built at ~250 K and ~1e5 Pa in SI units.
    assert 240.0 < float(fields["temperature"].mean()) < 260.0
    assert 9.0e4 < float(fields["surface_pressure"].mean()) < 1.1e5
    assert float(jnp.abs(fields["u"]).mean()) < 5.0


def test_si_increments_to_modal_zero_maps_to_zero(tiny_bundle, tiny_state):
    layer_count = tiny_bundle.layer_count
    nodal = tiny_bundle.coords.horizontal.nodal_shape
    zeros = jnp.zeros((layer_count, *nodal))
    dz, dd, dt = corrector.si_increments_to_modal(
        zeros,
        zeros,
        zeros,
        coords=tiny_bundle.coords,
        physics_specs=tiny_bundle.physics_specs,
    )
    assert dz.shape == tiny_state.vorticity.shape
    assert dd.shape == tiny_state.divergence.shape
    assert dt.shape == tiny_state.temperature_variation.shape
    np.testing.assert_array_equal(np.asarray(dz), 0.0)
    np.testing.assert_array_equal(np.asarray(dd), 0.0)
    np.testing.assert_array_equal(np.asarray(dt), 0.0)


def test_free_step_fn_advances_finite(tiny_bundle, tiny_state):
    step = rollout.build_step_fn(tiny_bundle)
    stepped = jax.jit(step)(tiny_state)
    for leaf in jax.tree_util.tree_leaves(stepped):
        assert bool(jnp.all(jnp.isfinite(leaf)))
    # The dycore must actually do something.
    assert not np.array_equal(
        np.asarray(stepped.temperature_variation),
        np.asarray(tiny_state.temperature_variation),
    )

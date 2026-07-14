# Copyright 2026 dynamaxx

"""Acceptance tests for the tutorial exercises. All marked `exercise`.

Work through them in order; each unlocks the next:

    JAX_PLATFORMS=cpu uv run pytest tests/nncorr -m exercise -k mlp -q
    JAX_PLATFORMS=cpu uv run pytest tests/nncorr -m exercise -k features -q
    JAX_PLATFORMS=cpu uv run pytest tests/nncorr -m exercise -k identity -q
    JAX_PLATFORMS=cpu uv run pytest tests/nncorr -m exercise -k rollout -q
    JAX_PLATFORMS=cpu uv run pytest tests/nncorr -m exercise -k "adam or clip" -q

They fail with NotImplementedError until you write the code, then they
fail with real assertions until you write it CORRECTLY.
"""

import jax
import jax.numpy as jnp
import numpy as np
import pytest

from dynamaxx.nncorr import corrector, features, mlp, rollout, train
from dynamaxx.nncorr.features import FeatureSpec

pytestmark = pytest.mark.exercise


# ----------------------------------------------------------------- EX 1: MLP


def _reference_gelu(x: np.ndarray) -> np.ndarray:
    # jax.nn.gelu default is the tanh approximation.
    return 0.5 * x * (1.0 + np.tanh(np.sqrt(2.0 / np.pi) * (x + 0.044715 * x**3)))


def test_mlp_apply_matches_numpy_reference():
    key = jax.random.PRNGKey(1)
    params = mlp.init_mlp_params(key, 7, (11, 5), 3)
    # Give the zero final layer real values so the test has teeth.
    params[-1]["w"] = jax.random.normal(jax.random.PRNGKey(2), (5, 3)) * 0.3
    params[-1]["b"] = jnp.asarray([0.1, -0.2, 0.3])

    x = np.asarray(
        jax.random.normal(jax.random.PRNGKey(3), (4, 6, 7)), dtype=np.float64
    )
    expected = x
    for i, layer in enumerate(params):
        expected = expected @ np.asarray(layer["w"]) + np.asarray(layer["b"])
        if i < len(params) - 1:
            expected = _reference_gelu(expected)

    actual = mlp.mlp_apply(params, jnp.asarray(x, jnp.float32))
    assert actual.shape == (4, 6, 3)
    np.testing.assert_allclose(np.asarray(actual), expected, atol=2e-5)


def test_mlp_apply_zero_final_layer_outputs_zero():
    params = mlp.init_mlp_params(jax.random.PRNGKey(4), 9, (16,), 5)
    x = jax.random.normal(jax.random.PRNGKey(5), (10, 9))
    out = mlp.mlp_apply(params, x)
    np.testing.assert_array_equal(np.asarray(out), 0.0)


def test_mlp_apply_is_jit_and_grad_safe():
    params = mlp.init_mlp_params(jax.random.PRNGKey(6), 4, (8,), 2)

    def scalar_loss(p, x):
        return jnp.sum(mlp.mlp_apply(p, x) ** 2)

    x = jax.random.normal(jax.random.PRNGKey(7), (3, 4))
    grads = jax.jit(jax.grad(scalar_loss))(params, x)
    # Zero final layer => dL/d(final w) is zero only if outputs are zero,
    # and dL/d(hidden) must ALSO be zero (chain through zero weights).
    for leaf in jax.tree_util.tree_leaves(grads):
        assert bool(jnp.all(jnp.isfinite(leaf)))


# ------------------------------------------------------------ EX 2: features


def test_assemble_features_contract(tiny_bundle):
    layer_count = tiny_bundle.layer_count
    nodal = tiny_bundle.coords.horizontal.nodal_shape
    spec = FeatureSpec(layer_count=layer_count)

    fields = {
        "temperature": jnp.stack(
            [jnp.full(nodal, 250.0 + 10.0 * k) for k in range(layer_count)]
        ),
        "u": jnp.stack([jnp.full(nodal, float(k)) for k in range(layer_count)]),
        "v": jnp.stack([jnp.full(nodal, -float(k)) for k in range(layer_count)]),
        "surface_pressure": jnp.full(nodal, 1.0e5 * float(np.exp(0.1))),
    }
    state_dim = spec.state_dim
    mean = jnp.zeros((state_dim,))
    std = jnp.ones((state_dim,))
    mean = mean.at[0].set(250.0)  # T at layer 0 standardizes to zero
    std = std.at[state_dim - 1].set(0.05)  # log-pressure entry

    static_stack = features.static_features(
        tiny_bundle.longitude, tiny_bundle.latitude
    )
    out = features.assemble_features(fields, static_stack, mean, std)

    assert out.shape == (*nodal, spec.feature_dim)
    assert out.dtype == jnp.float32
    np.testing.assert_allclose(np.asarray(out[..., 0]), 0.0, atol=1e-5)
    np.testing.assert_allclose(
        np.asarray(out[..., 1]), 260.0, atol=1e-4
    )  # unshifted T layer 1
    np.testing.assert_allclose(
        np.asarray(out[..., layer_count]), 0.0, atol=1e-6
    )  # u layer 0
    np.testing.assert_allclose(
        np.asarray(out[..., 2 * layer_count + 1]), -1.0, atol=1e-6
    )  # v layer 1
    np.testing.assert_allclose(
        np.asarray(out[..., state_dim - 1]), 0.1 / 0.05, atol=1e-3
    )  # standardized log-pressure = 2
    np.testing.assert_allclose(
        np.asarray(out[..., state_dim:]),
        np.moveaxis(np.asarray(static_stack), 0, -1),
        atol=1e-6,
    )


# ----------------------------------------------------- EX 3: corrector filter


def _tiny_context(bundle) -> corrector.CorrectorContext:
    spec = FeatureSpec(layer_count=bundle.layer_count)
    return corrector.CorrectorContext(
        coords=bundle.coords,
        physics_specs=bundle.physics_specs,
        reference_temperature=bundle.reference_temperature,
        feature_spec=spec,
        static_stack=features.static_features(bundle.longitude, bundle.latitude),
        state_mean=jnp.concatenate(
            [
                jnp.full((bundle.layer_count,), 250.0),  # T
                jnp.zeros((2 * bundle.layer_count,)),  # u, v
                jnp.zeros((1,)),  # log-pressure
            ]
        ),
        state_std=jnp.concatenate(
            [
                jnp.full((bundle.layer_count,), 30.0),
                jnp.full((2 * bundle.layer_count,), 15.0),
                jnp.full((1,), 0.05),
            ]
        ),
        step_seconds_si=900.0,
    )


def test_corrector_identity_at_zero_init(tiny_bundle, tiny_state):
    ctx = _tiny_context(tiny_bundle)
    params = mlp.init_mlp_params(
        jax.random.PRNGKey(8),
        ctx.feature_spec.feature_dim,
        (32,),
        ctx.feature_spec.output_dim,
    )
    nn_filter = corrector.make_nn_correction_filter(params, ctx)
    filtered = nn_filter(tiny_state, tiny_state)
    # Bit-exact identity: adding a zero increment must not change any leaf.
    for before, after in zip(
        jax.tree_util.tree_leaves(tiny_state),
        jax.tree_util.tree_leaves(filtered),
        strict=True,
    ):
        np.testing.assert_array_equal(np.asarray(before), np.asarray(after))


def test_corrector_increments_shapes_and_magnitude(tiny_bundle, tiny_state):
    ctx = _tiny_context(tiny_bundle)
    params = mlp.init_mlp_params(
        jax.random.PRNGKey(9),
        ctx.feature_spec.feature_dim,
        (32,),
        ctx.feature_spec.output_dim,
    )
    # Force a nonzero, O(1)-bounded output through the final layer bias.
    params[-1]["b"] = jnp.ones((ctx.feature_spec.output_dim,))
    dz, dd, dt = corrector.corrector_increments(params, tiny_state, ctx)
    assert dz.shape == tiny_state.vorticity.shape
    assert dd.shape == tiny_state.divergence.shape
    assert dt.shape == tiny_state.temperature_variation.shape
    for leaf in (dz, dd, dt):
        assert bool(jnp.all(jnp.isfinite(leaf)))
    assert float(jnp.abs(dt).max()) > 0.0

    # Physical scale check: unit NN output => ~0.052 K per 900 s step.
    from dynamaxx.dycore.models.dinosaur.adapter import _unit_factor

    kelvin = _unit_factor(tiny_bundle.physics_specs, "kelvin")
    grid = tiny_bundle.coords.horizontal
    dt_nodal_kelvin = grid.to_nodal(dt) / kelvin
    expected = corrector.TEMPERATURE_TENDENCY_SCALE_SI * 900.0
    np.testing.assert_allclose(
        np.asarray(dt_nodal_kelvin),
        expected,
        rtol=2e-2,
        atol=2e-4,
    )


# ------------------------------------------------------------- EX 5: rollout


def test_rollout_loss_grad_finite_and_nonzero(tiny_bundle, tiny_state):
    ctx = _tiny_context(tiny_bundle)
    params = mlp.init_mlp_params(
        jax.random.PRNGKey(10),
        ctx.feature_spec.feature_dim,
        (16,),
        ctx.feature_spec.output_dim,
    )

    target = corrector.decode_nodal_si(
        tiny_state,
        coords=tiny_bundle.coords,
        physics_specs=tiny_bundle.physics_specs,
        reference_temperature=tiny_bundle.reference_temperature,
    )

    def loss_fn(p):
        return rollout.rollout_loss(
            p,
            tiny_state,
            [target, target],
            bundle=tiny_bundle,
            make_filter=lambda q: corrector.make_nn_correction_filter(q, ctx),
            inner_steps=4,
            remat_lengths=(2, 2),
        )

    loss, grads = jax.value_and_grad(loss_fn)(params)
    assert np.isfinite(float(loss))
    assert float(loss) > 0.0  # the free core drifts away from the target
    leaves = jax.tree_util.tree_leaves(grads)
    assert all(bool(jnp.all(jnp.isfinite(leaf))) for leaf in leaves)
    total = sum(float(jnp.abs(leaf).sum()) for leaf in leaves)
    assert total > 0.0, (
        "gradients are identically zero — the NN filter is probably not in "
        "the differentiation path (rebuild the filter from params INSIDE "
        "the loss)"
    )


# ---------------------------------------------------------- EX 6: optimizer


def test_adam_matches_numpy_reference():
    params = {"a": jnp.asarray([1.0, -2.0]), "b": {"c": jnp.asarray([[3.0]])}}
    grads = {"a": jnp.asarray([0.5, 0.5]), "b": {"c": jnp.asarray([[-1.0]])}}
    moments = (
        jax.tree_util.tree_map(jnp.zeros_like, params),
        jax.tree_util.tree_map(jnp.zeros_like, params),
    )
    lr, b1, b2, eps = 1e-2, 0.9, 0.999, 1e-8

    new_params, (m, v) = train.adam_update(
        params, grads, moments, jnp.asarray(0), learning_rate=lr
    )
    new_params, (m, v) = train.adam_update(
        new_params, grads, (m, v), jnp.asarray(1), learning_rate=lr
    )

    def numpy_adam(p, g):
        m = np.zeros_like(p)
        v = np.zeros_like(p)
        for t in (1, 2):
            m = b1 * m + (1 - b1) * g
            v = b2 * v + (1 - b2) * g**2
            m_hat = m / (1 - b1**t)
            v_hat = v / (1 - b2**t)
            p = p - lr * m_hat / (np.sqrt(v_hat) + eps)
        return p

    np.testing.assert_allclose(
        np.asarray(new_params["a"]),
        numpy_adam(np.asarray([1.0, -2.0]), np.asarray([0.5, 0.5])),
        rtol=1e-6,
    )
    np.testing.assert_allclose(
        np.asarray(new_params["b"]["c"]),
        numpy_adam(np.asarray([[3.0]]), np.asarray([[-1.0]])),
        rtol=1e-6,
    )


def test_clip_by_global_norm():
    grads = {"a": jnp.asarray([3.0, 4.0]), "b": jnp.zeros(2)}  # norm 5
    clipped = train.clip_by_global_norm(grads, 1.0)
    np.testing.assert_allclose(np.asarray(clipped["a"]), [0.6, 0.8], rtol=1e-6)
    untouched = train.clip_by_global_norm(grads, 10.0)
    np.testing.assert_allclose(np.asarray(untouched["a"]), [3.0, 4.0], rtol=1e-6)
    zeros = jax.tree_util.tree_map(jnp.zeros_like, grads)
    all_zero = train.clip_by_global_norm(zeros, 1.0)
    for leaf in jax.tree_util.tree_leaves(all_zero):
        assert bool(jnp.all(jnp.isfinite(leaf)))

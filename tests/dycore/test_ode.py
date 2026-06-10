import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.dycore.ode import euler_step, integrate, rk4_step


def test_euler_step_integrates_constant_tendency():
    state = jnp.array([1.0, 2.0], dtype=jnp.float32)

    def tendency(state, time):
        del time
        return 3.0 * jnp.ones_like(state)

    next_state = euler_step(tendency, state, time=0.0, step_seconds=2.0)

    np.testing.assert_allclose(next_state, jnp.array([7.0, 8.0]))


def test_rk4_step_matches_fourth_order_linear_decay_polynomial():
    state = jnp.array([2.0], dtype=jnp.float32)
    decay_rate = 0.25
    step_seconds = 4.0

    def tendency(state, time):
        del time
        return -decay_rate * state

    next_state = rk4_step(tendency, state, time=0.0, step_seconds=step_seconds)
    z = -decay_rate * step_seconds
    expected = state * (1 + z + z**2 / 2 + z**3 / 6 + z**4 / 24)

    np.testing.assert_allclose(next_state, expected, rtol=1e-6)


def test_integrate_returns_leading_trajectory_axis_with_initial_state():
    state = jnp.array([1.0, 2.0], dtype=jnp.float32)

    def tendency(state, time):
        del time
        return jnp.ones_like(state)

    trajectory = integrate(
        tendency,
        state,
        steps=3,
        step_seconds=2.0,
        method="euler",
    )

    expected = jnp.array(
        [
            [1.0, 2.0],
            [3.0, 4.0],
            [5.0, 6.0],
            [7.0, 8.0],
        ],
        dtype=jnp.float32,
    )
    np.testing.assert_allclose(trajectory, expected)


def test_integrate_can_omit_initial_state():
    state = jnp.array([1.0], dtype=jnp.float32)

    def tendency(state, time):
        del time
        return jnp.ones_like(state)

    trajectory = integrate(
        tendency,
        state,
        steps=2,
        step_seconds=1.0,
        method="euler",
        include_initial=False,
    )

    np.testing.assert_allclose(trajectory, jnp.array([[2.0], [3.0]]))


def test_integrate_works_inside_jit():
    def rollout(state):
        def tendency(state, time):
            del time
            return -state

        return integrate(
            tendency,
            state,
            steps=2,
            step_seconds=0.1,
            method="rk4",
        )

    trajectory = jax.jit(rollout)(jnp.array([1.0], dtype=jnp.float32))

    assert trajectory.shape == (3, 1)
    np.testing.assert_allclose(trajectory[-1], jnp.exp(jnp.array([-0.2])), rtol=1e-6)

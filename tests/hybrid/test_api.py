import jax
import jax.numpy as jnp
import numpy as np

from dynamaxx.hybrid.api import HybridState, HybridStepDiagnostics


def test_state_and_diagnostics_are_jax_pytrees():
    state = HybridState(core={"value": jnp.asarray(2.0)})
    diagnostics = HybridStepDiagnostics(
        nodal_tendency={"value": jnp.asarray(0.5)},
    )

    def evaluate(input_state, input_diagnostics):
        return (
            input_state.core["value"]
            + input_diagnostics.nodal_tendency["value"]
        )

    result = jax.jit(evaluate)(state, diagnostics)

    np.testing.assert_allclose(result, 2.5)


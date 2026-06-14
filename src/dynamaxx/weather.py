# Copyright 2026 dynamaxx

from collections.abc import Sequence
from dataclasses import dataclass

import jax
import jax.numpy as jnp
import numpy as np


@jax.tree_util.register_pytree_node_class
@dataclass(frozen=True)
class WeatherState:
    """Named weather variables with longitude-latitude spatial axes.

    Values are shaped as (*leading, variable, longitude, latitude). The leading
    axes may contain lead time, initialization time, ensemble member, or any
    other model-specific batch axes.
    """

    values: jax.Array
    variables: tuple[str, ...]

    def __post_init__(self):
        values = jnp.asarray(self.values)
        variables = tuple(str(variable) for variable in self.variables)
        assert values.ndim >= 3
        assert values.shape[-3] == len(variables)
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "variables", variables)

    @property
    def leading_shape(self) -> tuple[int, ...]:
        """Return axes before variable, longitude, and latitude."""
        return tuple(self.values.shape[:-3])

    @property
    def spatial_shape(self) -> tuple[int, int]:
        """Return longitude-latitude shape."""
        longitude_count, latitude_count = self.values.shape[-2:]
        return int(longitude_count), int(latitude_count)

    def variable_indices(self, variables: Sequence[str]) -> np.ndarray:
        """Return integer indices for variables in the current state."""
        variable_to_index = {
            variable: variable_index
            for variable_index, variable in enumerate(self.variables)
        }
        missing_variables = [
            variable for variable in variables if variable not in variable_to_index
        ]
        assert not missing_variables, f"unknown variables {missing_variables}"
        return np.asarray(
            [variable_to_index[variable] for variable in variables],
            dtype=np.int64,
        )

    def select(self, variables: Sequence[str]) -> "WeatherState":
        """Return a state containing variables in the requested order."""
        variables = tuple(str(variable) for variable in variables)
        indices = jnp.asarray(self.variable_indices(variables), dtype=jnp.int32)
        values = jnp.take(self.values, indices, axis=-3)
        return WeatherState(values=values, variables=variables)

    def with_values(self, values: jax.Array) -> "WeatherState":
        """Return a new state with the same variable names and new values."""
        return WeatherState(values=values, variables=self.variables)

    def tree_flatten(self):
        """Return dynamic and static PyTree components for JAX transforms."""
        return (self.values,), self.variables

    @classmethod
    def tree_unflatten(cls, variables: tuple[str, ...], children):
        """Rebuild a state from JAX PyTree components."""
        (values,) = children
        return cls(values=values, variables=variables)

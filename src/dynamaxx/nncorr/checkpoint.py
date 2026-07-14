# Copyright 2026 dynamaxx

"""Minimal pytree checkpointing to .npz — no orbax, no pickle.

A params pytree flattens to (leaves, treedef). We save leaves keyed by their
tree path; to load, we flatten a TEMPLATE pytree with the same structure and
match paths. Loading therefore requires code that can rebuild the structure
— which is exactly the pure-functional discipline: the checkpoint stores
numbers, the program stores structure.
"""

from __future__ import annotations

import jax
import jax.numpy as jnp
import numpy as np


def _path_keys(tree) -> list[str]:
    flat, _ = jax.tree_util.tree_flatten_with_path(tree)
    return [jax.tree_util.keystr(path) for path, _ in flat]


def save_pytree(path: str, tree) -> None:
    """Save all array leaves of `tree` into a compressed .npz at `path`."""
    flat, _ = jax.tree_util.tree_flatten_with_path(tree)
    arrays = {
        jax.tree_util.keystr(key_path): np.asarray(leaf) for key_path, leaf in flat
    }
    np.savez_compressed(path, **arrays)


def load_pytree(path: str, template):
    """Load leaves from `path` into the structure of `template`.

    Every leaf of `template` must exist in the file with identical shape;
    dtypes are cast to the template leaf dtype.
    """
    with np.load(path) as data:
        flat, treedef = jax.tree_util.tree_flatten_with_path(template)
        leaves = []
        for key_path, template_leaf in flat:
            key = jax.tree_util.keystr(key_path)
            assert key in data, f"missing checkpoint leaf {key}"
            loaded = data[key]
            template_leaf = jnp.asarray(template_leaf)
            assert loaded.shape == template_leaf.shape, (
                f"{key}: checkpoint shape {loaded.shape} != "
                f"template shape {template_leaf.shape}"
            )
            leaves.append(jnp.asarray(loaded, dtype=template_leaf.dtype))
    return jax.tree_util.tree_unflatten(treedef, leaves)

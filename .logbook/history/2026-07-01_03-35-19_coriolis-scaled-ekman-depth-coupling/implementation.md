# Implementation: coriolis-scaled-ekman-depth-coupling

- Baseline commit: `2d592c9fb419a0a157fd6d0b8cba8ff862bdfc46`
- Candidate commit: `b40f5515ec79abeec4f10db4addfd0abbe44da13`
- Candidate model: `dino_ri2m_ekman_depth`
- Incumbent model: `dino_ri2m_ekman_coupled`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Summary

The candidate adds a side-by-side `dino_ri2m_ekman_depth` model derived from the accepted coupled Ekman incumbent. The incumbent fixed 2000 m Ekman stress depth remains unchanged unless the new `use_coriolis_scaled_ekman_depth` selector is enabled.

When enabled, the coupled Ekman surface filter computes a bounded neutral depth from local friction velocity over a floored Coriolis magnitude, applies smooth hypsometric vertical weights, and falls back to the fixed-depth incumbent path when the new depth or height diagnostics are invalid. The candidate keeps the incumbent drag coefficient, wind increment caps, pressure increment cap, equatorial pumping taper, area-neutral projections, and pressure coupling structure.

## Tests

- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'ekman_depth or ekman_coupled' tests/dycore/models/dinosaur/test_dependency.py -k 'ekman_depth or registered' tests/dycore/test_registry.py -k 'ekman_depth or default_dycore_models'`: passed, `7 passed, 207 deselected`.
- `uv run pytest`: passed, `280 passed, 2 skipped`.

## Known Limitations

The depth coefficient is fixed before scoring and intentionally not tuned against iteration or validation metrics. The implementation preserves the forecast contract and adds no evaluation-protocol changes.

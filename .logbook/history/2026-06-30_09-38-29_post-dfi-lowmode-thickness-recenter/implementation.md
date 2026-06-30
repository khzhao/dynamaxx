# Implementation Report

## Identity

- Proposal slug: post-dfi-lowmode-thickness-recenter
- Candidate model: dino_ri2m_postdfi_thick
- Incumbent model: dino_ri2m_ekman_coupled
- Baseline commit: 399e133aa14b83cd8fd3dd16f48d267df8a84bf5
- Candidate commit: not committed; candidate is represented by the working-tree diff and `candidate.diff`
- Implemented at: 2026-06-30T10:08:57Z

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`

## Summary

The candidate registers `dino_ri2m_postdfi_thick` as a side-by-side model derived from the accepted `dino_ri2m_ekman_coupled` incumbent. It adds a default-disabled `apply_post_dfi_low_mode_thickness_recenter` selector and enables it only in the new candidate factory.

When enabled, the trajectory builder runs the incumbent DFI initializer unchanged, then applies one guarded initialization-time temperature-only correction before positive-time rollout. The correction compares DFI-diagnosed low-mode Z500 and 300-700 hPa thickness residuals against same-time analysis geopotential channels. It applies a capped, area-mean-free, middle-column temperature increment only when diagnostics are finite, pressure bracketing is valid, residuals are bounded and sign-consistent, the increment has material effect, and dry static stability remains above the fixed floor. Vorticity, divergence, log surface pressure, tracers, sim time, positive-time rollout filters, output variables, metrics, splits, and lead schedule are unchanged.

## Tests Run

- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -q -k "post_dfi_thickness"`: passed, 7 passed and 152 deselected.
- `uv run pytest tests/dycore/models/dinosaur tests/dycore/test_registry.py`: initially failed because `tests/dycore/models/dinosaur/test_dependency.py` lacked the new registry key; after updating that expected list, passed with 215 passed and 1 skipped.
- `uv run pytest`: passed with 281 passed and 2 skipped.

## Known Limitations

- The small non-JIT smoke fixture does not request `geopotential_500` because that tiny grid produces nonfinite geopotential diagnostics independent of the candidate correction. The fixed WeatherBench2 evaluation still uses the unchanged target-variable protocol, including `geopotential_500`.
- Evaluation gates have not been run in this implementation phase. Scoring will be recorded separately in `scores.json` and `scoring_notes.md`.

# Implementation Record

## Identity

- Proposal slug: depth-weighted-orographic-lift-wind
- Candidate model name: dino_ri2m_ekman_depth_orolift_lwind
- Incumbent model name: dino_ri2m_ekman_depth_orolift_theta
- Baseline commit: 2ced7296aeeb4433074436865395ca7b4f622500
- Candidate commit: db2387935aa0937eb8669de20843dc3caaccb115

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Added a default-off `use_depth_weighted_orographic_lift_wind` selector to the Dinosaur adapter. When enabled for the candidate model, `_orographic_lift_theta_tendency_step_filter` uses a fixed lower-column weighted mean wind over the lower sigma-envelope support for terrain-lift forcing and weak-flow taper, with finite and degenerate diagnostics falling back to the incumbent lowest-layer wind. The existing low-mode terrain, latitude taper, forecast-time ramp, area-neutral projection, modal projection, per-step temperature cap, forecast contract, and incumbent model remain unchanged.

Registered side-by-side candidate model `dino_ri2m_ekman_depth_orolift_lwind`, derived from `orographic_lift_theta_dinosaur_dycore_model()`.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | No files changed by formatter. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | All checks passed. |
| `uv run pytest tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py` | 0 | `228 passed`. |
| `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind` | 0 | Primary `-0.12943824136377413`; issues `0`; records `120`; `failed=False` in CLI output. |
| `uv run pytest` | 0 | `294 passed, 2 skipped`. |

## Repair Attempts

- Failure observed: Implementer reported an initial focused pytest failure due only to strict float32 equality tolerance in the new weighted-helper test.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: relaxed the focused helper assertion to appropriate float32 allclose tolerance.
- Follow-up command and result: final focused pytest passed with `228 passed`; full pytest passed with `294 passed, 2 skipped`; fast eval passed cleanly.

## Known Limitations

- Limitation: Fixed lower-column weights are intentionally conservative and hard-coded to avoid score tuning. The candidate may weaken useful terrain-lift forcing if the lowest layer is already the best resolved incoming-flow estimate.

## Rollback Notes

If rejected, revert only this candidate's source and test edits with `git apply -R .logbook/history/2026-07-02_20-06-48_depth-weighted-orographic-lift-wind/candidate.diff`. Leave unrelated `gifs/`, prior history, accepted leaderboard state, and raw eval outputs untouched unless explicitly instructed otherwise.

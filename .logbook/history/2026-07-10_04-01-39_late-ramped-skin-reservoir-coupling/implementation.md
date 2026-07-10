# Implementation Record

## Identity

- Proposal slug: late-ramped-skin-reservoir-coupling
- Candidate model name: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin
- Incumbent model name: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m
- Baseline commit: ac8438a42bec2e0c99300b2ccd13d19e22e3c993
- Candidate commit: b92c07d2f054bd34cb90d36592501c5ff74c5991

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Implemented one side-by-side current-incumbent descendant with an internal land
skin/deep-temperature pair carried outside `primitive_equations.State`. The
pair is initialized from post-DFI lowest-layer air, excluded from tracers and
outputs, and updated after each resolved rollout step.

The fixed smoothstep coupling is exactly zero through 120 forecast hours,
equals one half at 180 hours, and is full at 240 hours. The implementation
reuses the rejected reservoir's fixed transfer coefficient, exchange depth,
minimum e-folding time, heat-capacity ratio, deep restore time, per-step cap,
and land threshold without tuning. Capped air exchange uses the same exchanged
amount for the opposite skin response, preserving the area-mean combined
air/skin energy after modal projection. Invalid state, mask, shape, or finite
diagnostics return the exact incumbent state and unchanged reservoir.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'late_skin or land_skin_reservoir'` | 0 | 6 passed, 179 deselected |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py -k 'late_skin or land_skin_reservoir or late_ramped or canonical or lists'` | 0 | 4 passed, 63 deselected |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | All checks passed |
| `git diff --check` | 0 | No whitespace errors |
| `uv run pytest` | 0 | 318 passed, 2 skipped in 311.71 seconds |
| `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin --workers 4` | 0 | Primary `-0.11041836504747159`; diagnostics clean; 120 records |
| `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin --workers 4` | 0 | Primary `-0.1102658536572533`; diagnostics clean; iteration gate passed |
| `uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin --workers 4` | 0 | Primary `-0.11137528326510353`; diagnostics clean; acceptance gate passed |

## Repair Attempts

- Failure observed: Ruff reported import ordering in the focused primitive test.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: reordered the newly added imports without changing behavior.
- Follow-up command and result: Ruff, focused tests, and full pytest passed.

## Known Limitations

- The original always-active reservoir failed T2m guardrails, with its worst
  single-lead regression at the same 240-hour point where this candidate's ramp
  reaches full strength.
- The accepted candidate is intentionally inactive through 120 hours and is
  specialized to the current Dinosaur rollout wrapper rather than a general
  land-surface model.

## Rollback Notes

The complete six-file source/test patch is saved as `candidate.diff` with
SHA-256
`ee0dd557c5c096805e19c2117e316a1878789e8b05f28de54ce20c58fd0f19e9`.
Its hash matched the tracked diff before acceptance. The patch was retained as
the immutable implementation record and committed as
`b92c07d2f054bd34cb90d36592501c5ff74c5991`. If this accepted mechanism is
later reverted, reverse that source commit without touching subsequent
experiments or the user-owned `gifs/` directory.

# Implementation Record

## Identity

- Proposal slug: prognostic-skin-ri2m-lower-boundary
- Candidate model name: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri
- Incumbent model name: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin
- Baseline commit: 3621797069bc8cd4d7845586b0b6659c045676c9
- Candidate commit: 3fb32ff048b00b779d7e16a2c72e728866a4f4ba

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Implemented one side-by-side descendant of the accepted late-skin incumbent.
The candidate retains the existing `(state, skin)` scan frames only for output
packing; the integration carry, step function, filters, DFI, atmospheric state,
and skin evolution are unchanged. Skin remains absent from primitive state,
tracers, emitted variables, and the public deterministic forecast contract.

At valid land points, the observer constructs a bounded surface-layer estimate
from the prognostic skin potential temperature and the incumbent
pressure-thickness lower-band temperature/wind reference. It diagnoses lower
reference height hydrostatically, forms a clipped bulk Richardson number, and
interpolates from skin toward the lower atmospheric reference at 2 m with the
existing stability limiter. The estimate reuses the incumbent RI2m departure
cap and is blended with incumbent T2m using land fraction and the accepted ramp
that is zero through 120 hours and full at 240 hours. Missing skin, time, mask,
unsupported geometry, invalid land/pressure/temperature values, nonfinite
diagnostics, ocean points, and zero ramp return exact incumbent T2m. Every
non-T2m output remains unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'prognostic_skin_ri2m'` | 0 | 5 passed, 185 deselected in 14.47s |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py -k 'prognostic_skin or skri or canonical or lists'` | 0 | 4 passed, 65 deselected in 2.11s |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | All checks passed |
| `git diff --check` | 0 | No whitespace errors |
| `uv run pytest` | 0 | 325 passed, 2 skipped in 313.77s |
| `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri --workers 4` | not_run | Scorer-owned gate |

## Repair Attempts

- Failure observed: initial Ruff run found one import-order issue; an early
  no-JIT trajectory test also used an unnecessarily expensive full solver
  harness and was stopped after 134.79 seconds without an assertion failure.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: reordered the new import and replaced the expensive harness
  with a deterministic step that compares the exact incumbent and candidate
  atmospheric/skin carries without changing the behavior under test.
- Follow-up command and result: focused tests, Ruff, diff check, and full pytest
  all passed.

## Known Limitations

- This is a T2m-only observer experiment. It cannot improve MSLP, Z500, or U10,
  and retaining the skin trajectory increases temporary output-packing memory.
- The reduced prognostic skin is physically motivated but is not a complete
  surface-energy model; direct observer use may duplicate its atmospheric heat
  exchange signal or overstate stable land departures.

## Rollback Notes

The exact six-file source/test patch is saved as `candidate.diff` with SHA-256
`fc98be9af6ddbda66636fb89717b7339d29f7fa23f4adfe8ba139178af233758`.
It matched the live diff before acceptance and was retained in accepted source
commit `3fb32ff048b00b779d7e16a2c72e728866a4f4ba`. A future rollback should
reverse that commit without touching later experiments or the user-owned
`gifs/` directory.

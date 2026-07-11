# Implementation Record

## Identity

- Proposal slug: zero-mean-radiative-land-skin-energy
- Candidate model name: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori_rskin
- Incumbent model name: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori
- Baseline commit: b3acd8d84198fab11a43aa9b029f51087be4caa6
- Accepted incumbent source commit: ea124f2d1b43e8e9e54efcbe0abf05e80f6b8001
- Candidate commit: 8d8b2cba4399bf9f35689c4e55855e2436d367a6

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

`radiation.py` did not need modification because its existing `SolarRadiation`
API supports the frozen implementation.

## Implementation Summary

Added one default-false side-by-side selector. The candidate evaluates existing
TOA solar radiation at each sample's own initial-time phase, combines the
frozen absorbed-shortwave and deep-minus-skin longwave terms, removes each
active-land area-weighted mean separately, and converts the zero-net power to a
private skin-temperature increment using forecast density and the accepted
heat-capacity geometry. It applies the unchanged 120-240 h ramp and one common
field scale under the accepted `0.05 K` cap. Atmospheric state, deep restore,
air-skin exchange, ocean anchor, RI2m observer, residual memory, and non-T2m
outputs remain on the incumbent path.

Frozen candidate diff SHA-256:
`a84e6b7448200603fb42d5b213723c1e083956cd8057107a9a349c2413b62594`.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| Ruff on all six changed Python files | 0 | Passed. |
| Added radiative behavior tests | 0 | 25 passed. |
| Existing/new land-skin and observer tests | 0 | 58 passed. |
| Registry and dependency tests | 0 | 75 passed. |
| Compiled multi-initial phase and missing-anchor regressions | 0 | Passed. |
| `uv run pytest` | 0 | 379 passed, 2 skipped in 8m26s. |
| `git diff --check` | 0 | Passed on the frozen diff. |
| `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori_rskin` | 0 | Candidate-only sanity gate passed with clean diagnostics. |
| `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori_rskin --workers 4` | 0 | Candidate improved the cached incumbent by `+0.005211103590004776`; fixed guardrails passed. |
| `uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori_rskin --workers 4` | 0 | Single permitted validation run improved the cached incumbent by `+0.005298897431801106`; fixed guardrails passed. |

## Repair Attempts

- Failure observed: an early-ramp assertion inspected the scanner's 180-hour
  final carry rather than the saved leads through 120 hours.
- Implementer-owned failure: yes, test expectation only.
- NaN/Inf forecast observed: no.
- Fix attempted: corrected the saved-lead assertion; added dynamic-offset and
  private-skin phase tests because the output observer can mask small skin
  differences; restored exact incumbent trajectory-call branching after a
  missing ocean anchor exposed positional-argument ambiguity.
- Follow-up command and result: focused suites, registry/dependency tests, final
  full pytest, Ruff, registry construction, and diff checks passed.

## Known Limitations

- The candidate uses clear-sky TOA phase and a reduced zero-net land energy
  closure, not clouds, soil moisture, snow, vegetation, or a full radiation
  scheme.
- It changes only private land-skin evolution and therefore expects score
  leverage primarily in late land T2m.

## Rollback Notes

If rejected, reverse only the frozen candidate diff across this iteration's permitted files, verify no tracked diff remains, retain ignored history/raw metrics locally, and do not commit rejected work.

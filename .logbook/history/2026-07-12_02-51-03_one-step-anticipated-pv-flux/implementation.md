# Implementation Record

## Identity

- Proposal slug: `one-step-anticipated-pv-flux`
- Candidate model name: `dino_rskin_apv`
- Incumbent model name: `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori_rskin`
- Baseline HEAD: `d48e1df095fbbfe6ccd2c64688c60b24e22a4d01`
- Accepted incumbent source commit: `8d8b2cba4399bf9f35689c4e55855e2436d367a6`
- Candidate source commit: `7174848c3641a43299fc5c2682bef2fc75f2ff89`
- Frozen proposal SHA-256: `b7dc7f90568b8e7699990ac65ebbccd3de7fb9d82ec886e59f896f2134a5f35e`
- Frozen candidate diff SHA-256: `c05bf8f247f386bd3148eec6ce33ee2ecc5f403d8073baab7ba0dce01ee30f94`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_anticipated_pv_flux.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

The frozen patch contains 704 insertions and 4 deletions. `git apply --check --reverse` succeeds against the implemented worktree, confirming that the patch captures all seven candidate files and can remove only this experiment.

## Implementation Summary

The candidate registers one side-by-side descendant of the accepted radiative-land-skin incumbent. Its positive-time primitive equation diagnoses a sigma-layer shallow-water PV proxy from current surface pressure, sigma thickness, relative vorticity, and the physical Coriolis field. It forms the existing spherical metric contraction of the PV gradient with the nodal wind, applies the frozen one-step anticipation sign, and adds the resulting perpendicular flux before the incumbent curl and divergence operators.

The selector defaults false. DFI constructs an exact incumbent equation with no APVM inputs. The existing symmetric Coriolis split, all thermodynamic and continuity tendencies, final wavenumber clipping, filters, observers, and accepted radiative land-skin state remain unchanged. One scalar validity predicate selects either the complete candidate curl/divergence pair or the complete incumbent pair.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| Dedicated APVM test module | 0 | 10 passed after final lint-only cleanup. |
| Related Dinosaur primitive-equation, dependency, APVM, and registry suite | 0 | 324 passed. |
| `uv run pytest` | 0 | 390 passed, 2 skipped before the final import-order/docstring-only test cleanup. No source behavior changed afterward, and the affected APVM module was rerun successfully. |
| Ruff over all seven changed files | 0 | Independently rerun after cleanup: all checks passed. |
| Python compilation | 0 | Implementer reported success. |
| `git diff --check` | 0 | Independently rerun after cleanup. |
| `git apply --check --reverse <candidate.diff>` | 0 | Frozen rollback patch verified. |
| `uv run dynamaxx-eval fast --model dino_rskin_apv` | not_run | Reserved for the Scorer. |

## Repair Attempts

- The Implementer replaced tuple-wide finiteness checks with componentwise checks compatible with JAX arrays.
- Independent review found Ruff import-order and public-test-docstring failures in the new test module despite the initial lint report.
- The bounded revision changed only test import ordering and docstrings. Ruff then passed on all seven files and the APVM module passed 10 tests in 9.33 seconds.
- No NaN or Inf forecast was observed during implementation testing.
- No scientific parameter, sign, operator, cap, mask, or fallback rule was revised.

## Known Limitations

- The closure is a sigma-layer shallow-water PV proxy, not full Ertel-PV conservation.
- Pointwise nodal work neutrality does not establish exact full-model energy conservation after pseudo-spectral transforms and the model's other operators.
- The candidate adds modal/nodal PV transforms and gradients to every positive-time explicit tendency evaluation, so runtime cost may increase.

## Rollback Notes

If rejected, reverse-apply `candidate.diff`. It removes the new test and restores the six tracked source/test files to the baseline while leaving protected `gifs/`, evaluation outputs, and ignored history untouched. Do not commit rejection records.

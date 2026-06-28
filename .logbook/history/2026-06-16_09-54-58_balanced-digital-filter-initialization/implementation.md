# Implementation Record

## Identity

- Proposal slug: balanced-digital-filter-initialization
- Candidate model name: dinosaur_dfi
- Incumbent model name: dinosaur
- Baseline commit: 4beb6c221f8655f80b6530713ffc75697e9c654e
- Candidate commit: cfdc344723cee1f267b892ddd924fc5d07b89f2d

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

The candidate adds an optional fixed short digital filter initialization pass to the Dinosaur primitive-equation adapter. When enabled, the adapter builds the same forecast equation and horizontal diffusion filters used by the main trajectory, nondimensionalizes a 6 hour time span and cutoff period, applies the existing Lanczos `time_integration.digital_filter_initialization` helper to each converted Dinosaur state, and then rolls out the normal forecast trajectory from that initialized state.

The canonical `dinosaur` model remains unchanged. The candidate is exposed side-by-side as `dinosaur_dfi` through the dycore registry and package exports, preserving the existing forecast input/output contract, deterministic evaluation gates, target variables, splits, and metrics.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/test_registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py` | 0 | 24 passed after replacing an impractical real no-jit DFI test with a focused monkeypatched contract test. |
| `uv run pytest` | 0 | 90 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi` | 0 | Diagnostics passed, issue count 0, primary score -1.2844866682514346. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi --workers 4` | 0 | Diagnostics passed, issue count 0, primary score -1.3208025947740873. |
| `uv run dynamaxx-eval validation --model dinosaur_dfi --workers 4` | 0 | Diagnostics passed, issue count 0, primary score -1.308334010223954. |
| `git diff --check` | 0 | No whitespace errors before commit. |

## Repair Attempts

- Failure observed: an initial no-jit test that exercised real DFI was interrupted after several minutes, making it unsuitable for the unit suite; a later targeted test exposed recursive trajectory wrapping.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no in accepted fast, iteration, or validation artifacts.
- Fix attempted: captured the pre-DFI `trajectory_fn` as `base_trajectory_fn` before wrapping, and used monkeypatched DFI tests to verify wiring without compiling the full reversible filter path in the unit suite.
- Follow-up command and result: targeted tests, full test suite, fast, iteration, and validation all passed.

## Known Limitations

- The DFI window and cutoff are fixed before scoring and were not tuned across experiments.
- DFI adds extra integration work before the scored trajectory; the fixed evaluation accepted the score improvement despite that cost.
- The candidate is a side-by-side registered model. The canonical `dinosaur` implementation remains available for comparison and rollback.

## Rollback Notes

Revert commit `cfdc344723cee1f267b892ddd924fc5d07b89f2d` to remove the accepted `dinosaur_dfi` candidate registration, adapter option, and tests. Preserve this history directory and raw evaluation artifacts when rolling back.

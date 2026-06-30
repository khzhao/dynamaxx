# Implementation Report

## Identity

- Proposal slug: time-centered-ekman-stress-pumping
- Candidate model: dino_ri2m_ekman_tcenter
- Incumbent model: dino_ri2m_ekman_coupled
- Baseline commit: 3fdb5437dfb22b191c9776a06ae6f0e537b75d2f
- Candidate commit: not committed; candidate is represented by the working-tree diff and `candidate.diff`
- Implemented at: 2026-06-30T13:44:26Z

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`

## Summary

The candidate registers `dino_ri2m_ekman_tcenter` as a side-by-side model derived from the accepted `dino_ri2m_ekman_coupled` incumbent. It adds a default-disabled `use_time_centered_ekman_coupled_closure` selector and enables it only in the new candidate factory.

When enabled, the accepted coupled Ekman surface filter diagnoses lowest-layer winds, lowest-layer temperature, and surface pressure from both `prev_state` and `next_state`, forms midpoint diagnostics from matching finite positive endpoints, computes the existing stress-pumping wind and pressure increments from those midpoint diagnostics, and applies the resulting increments to `next_state`. If previous, next, or midpoint diagnostics are invalid or shape-incompatible, the filter falls back to the incumbent endpoint closure rather than disabling the Ekman increment.

The implementation keeps the accepted drag coefficient, boundary-layer depth, vertical taper, equatorial taper, wind cap, pressure cap, pressure-per-wind cap, modal projection checks, area-neutral pressure projection, DFI path, WTG path, vertical-DSE path, T2m memory, RI2m diagnostics, target variables, lead days, and fixed evaluation protocols unchanged.

## Tests Run

- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -q -k "ekman_coupled or ekman_tcenter or registry"`: passed, 10 passed and 146 deselected.
- `uv run pytest tests/dycore/models/dinosaur tests/dycore/test_registry.py`: initially failed because `tests/dycore/models/dinosaur/test_dependency.py` lacked the new registry key; after updating that expected list, passed with 212 passed and 1 skipped.
- `uv run pytest`: passed with 278 passed and 2 skipped.
- `uv run dynamaxx-eval fast --model dino_ri2m_ekman_tcenter`: passed with `failed=False`, `issues=0`, and primary score `-0.16795463351583548`.

## Repair Attempts

- The Implementer reported one broader-suite failure in `test_dependency.py::test_dinosaur_is_registered_as_canonical_dycore_model`; Orchestrator added the missing `dino_ri2m_ekman_tcenter` registry key to that exact expected list.
- No implementation-owned focused test failures remained after the Implementer patch.

## Known Limitations

- Full fixed WeatherBench2 scoring is not included in this implementation record; it is recorded separately in `scores.json` and `scoring_notes.md`.
- The candidate intentionally tests one midpoint quadrature only. It does not tune midpoint weights, drag constants, caps, activation windows, or spatial masks.

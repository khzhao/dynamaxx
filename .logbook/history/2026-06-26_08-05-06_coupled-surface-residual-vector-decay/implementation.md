# Implementation Record

## Identity

- Proposal slug: coupled-surface-residual-vector-decay
- Candidate model name: dino_hsl2_mass_dse_wtg_vdse_ramp_sfc_vec
- Incumbent model name: dino_hsl2_mass_dse_wtg_vdse_ramp
- Baseline commit: ff40def55ac707e8915c840b856a0aaa3345b046
- Candidate commit: not committed before scoring

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Implemented a side-by-side registered candidate,
`dino_hsl2_mass_dse_wtg_vdse_ramp_sfc_vec`, derived from the accepted
pressure-ramped vertical-DSE WTG incumbent. The candidate adds an opt-in
post-trajectory residual selector that couples `2m_temperature` and
`10m_u_component_of_wind` residual decay as a scaled vector using fixed
temperature and wind residual scales. The candidate preserves vector direction
within each residual band and uses the existing stability-aware and
scale-separated decay machinery for the shared decay factors.

The implementation is output-only after the raw Dinosaur trajectory is
produced. It does not alter the forecast contract, prognostic dynamics, WTG,
vertical-DSE path, pressure gradients, DFI, diffusion, pressure-level outputs,
surface pressure, or humidity. Missing paired residual channels, nonfinite lead
hours, invalid scale splits, invalid decay diagnostics, or nonfinite vector
diagnostics fall back to the incumbent scale-separated near-surface residual
correction path.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | ---: | --- |
| `uv run ruff format --check <changed files>` | 1 | Initial implementer check found 3 files needing formatting. |
| `uv run ruff format <changed files>` | 0 | Implementer formatting pass. |
| `uv run ruff format --check <changed files>` | 0 | Formatting clean after repair. |
| `uv run ruff check <changed files>` | 0 | Lint clean. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | Focused tests passed: 195 passed. |
| `uv run pytest` | 0 | Implementer full-suite record: 261 passed, 2 skipped. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_sfc_vec` | 0 | Fast artifact verified: primary score -0.2413961488632447, diagnostics failed false, issue count 0, 120 metric rows. |
| `uv run python - <<'PY' ... registry.dycore_model_names/create_dycore_model ... PY` | 0 | Orchestrator verified candidate and incumbent registration/construction. |
| `git diff --check` | 0 | Orchestrator verified no whitespace errors. |

## Repair Attempts

- Failure observed: initial Ruff format check reported formatting changes were needed in 3 files.
- Implementer-owned failure: yes.
- NaN/Inf forecast observed: no.
- Fix attempted: ran repository formatter over the changed files.
- Follow-up command and result: Ruff format check, Ruff lint, focused pytest, full pytest, fast eval, and `git diff --check` all passed.

## Known Limitations

- For the valid coupled-vector path, land-sea-specific T2m-only residual decay is not applied because that would break the shared residual-vector direction. Invalid vector diagnostics still fall back exactly to the incumbent path, including incumbent land-sea behavior.
- The fast primary score was worse than the incumbent neighborhood, but fast is a sanity gate only. Fixed iteration scoring is required to decide the candidate.

## Rollback Notes

If rejected, apply the reverse of `candidate.diff` from this history directory
to revert only the source/test changes from this experiment. Preserve raw
evaluation outputs and this immutable history directory. The pre-existing
untracked `gifs/` directory is unrelated and must not be removed.

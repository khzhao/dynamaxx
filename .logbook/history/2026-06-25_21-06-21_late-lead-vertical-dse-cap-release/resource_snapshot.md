# Resource Snapshot

## Git And Worktree

- Baseline commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Baseline branch: `kzhao--codex`
- Pre-existing untracked files/directories: `gifs/`
- Candidate implementation files changed:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/test_registry.py`

## Machine Resources

- CPU count: 48
- Available RAM before implementation/scoring: 172 GiB
- GPU count: 4
- GPU memory: four NVIDIA L4 devices, about 22 GiB free each
- Repository/output filesystem free space: 4.1 TiB
- Selected evaluation workers: 4
- Worker rationale: below half of CPU count, within available RAM, and matches
  the repository's established fixed scoring setting for current candidates.

## Incumbent Cache

- Incumbent model: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Incumbent commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Cached iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Cached iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`
- Cached validation JSON: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Cached validation CSV: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`
- Cache validity: artifacts were present, readable, finite at the primary-score
  level, and contained the incumbent rows for target-variable and lead guardrail
  comparisons. Candidate source edits do not invalidate this cache under
  `roles/PROTOCOL.md` and `roles/SCORER.md`.

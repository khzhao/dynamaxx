# Resource Snapshot

## Baseline State

- Baseline commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Branch: `kzhao--codex`
- Baseline git status before implementation: tracked tree clean except
  pre-existing untracked `gifs/`.
- Selected ready proposal:
  `.logbook/research/ready/high-precision-spectral-transform-core.md`

## Incumbent Cache

- Incumbent model: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Iteration metrics JSON:
  `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Iteration metrics CSV:
  `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`
- Validation metrics JSON:
  `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Validation metrics CSV:
  `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`
- Cache policy: incumbent artifacts are valid by default because the requested
  incumbent is the leaderboard incumbent at the accepted commit. Candidate source
  edits do not invalidate this cache.

## Machine Snapshot

- CPUs available to the host: 48.
- Memory at pre-scoring snapshot: 181 GiB total, 171 GiB available.
- GPU snapshot after fast gate:
  - GPU 0 NVIDIA L4: 0 MiB used, 22566 MiB free, 0% utilization.
  - GPU 1 NVIDIA L4: 0 MiB used, 22566 MiB free, 0% utilization.
  - GPU 2 NVIDIA L4: 0 MiB used, 22566 MiB free, 0% utilization.
  - GPU 3 NVIDIA L4: 0 MiB used, 22566 MiB free, 0% utilization.
- Disk at pre-scoring snapshot: 4.8 TiB total, 4.1 TiB available.

## Evaluation Plan

- Full tests: `uv run pytest`.
- Fast sanity gate:
  `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec`.
- Iteration gate:
  `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec --workers 4`.
- Validation gate only if iteration promotes:
  `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_sht_highprec --workers 4`.
- Golden is not part of iterative model selection and must not be run.

# Resource Snapshot

## Identity

- Proposal slug: `recenter-before-wtg-filter-order`
- Candidate model name: `dino_hsl2_mass_dse_wtg_vdse_ramp_precenter_wtg`
- Incumbent model name: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Baseline commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Baseline git status: tracked tree clean; pre-existing untracked `gifs/`
  directory preserved.

## Machine Resources

- CPU count: `48`
- RAM: `181Gi` total, `171Gi` available at pre-implementation check.
- GPUs: four NVIDIA L4 GPUs, each reporting `23034 MiB` total and
  approximately `22566 MiB` free.
- Disk: `/dev/root` with `4.1T` free for repository, `outputs`, and
  `.logbook`.

## Worker Selection

- Selected evaluation workers: `4`
- Rationale: available RAM is above `128 GiB`, CPU count is `48`, and disk
  headroom is far above the `50 GiB` minimum. `--workers 4` follows the
  protocol's conservative default for this machine and matches recent accepted
  and rejected scoring runs.

## Incumbent Cache

- Leaderboard path: `.logbook/leaderboard.json`
- Incumbent commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Iteration score: `-0.2197104515448394`
- Validation score: `-0.21940899263836755`
- Iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`
- Validation JSON: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Validation CSV: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`
- Cache policy: reuse these accepted incumbent artifacts by default. Candidate
  source edits do not invalidate the cache. Rerun the incumbent only if these
  artifacts are missing, unreadable, nonfinite, incomplete, or incompatible with
  the fixed protocol fingerprint.

## Protected State

- Do not touch `gifs/`.
- Do not change fixed evaluation protocols, WeatherBench2 splits, target
  variables, lead times, metrics, or golden usage.
- Implement exactly the selected filter-order proposal.

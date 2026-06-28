# Resource Snapshot

## Identity

- Proposal slug: `narrow-core-tropical-wtg-envelope`
- Candidate model name: `dino_hsl2_mass_dse_wtg_vdse_ramp_wtg_narrow`
- Incumbent model name: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Baseline commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Baseline git status: tracked tree clean; pre-existing untracked `gifs/`
  directory preserved.

## Machine Resources

- CPU count: `48`
- RAM: `181Gi` total, `171Gi` available at pre-implementation check.
- GPUs: four NVIDIA L4 GPUs, each reporting `23034 MiB` total and
  approximately `22566 MiB` free before implementation.
- Disk: `/dev/root` with `4.1T` free for repository, `outputs`, and
  `.logbook`.

## Worker Selection

- Selected evaluation workers: `4`
- Rationale: local resources support the protocol's conservative `--workers 4`
  iteration setting.

## Incumbent Cache

- Leaderboard path: `.logbook/leaderboard.json`
- Incumbent commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Iteration score: `-0.2197104515448394`
- Validation score: `-0.21940899263836755`
- Iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`
- Validation JSON: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Validation CSV: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`
- Cache policy: incumbent artifacts were reused. Candidate source edits do not
  invalidate the accepted incumbent cache, and no cache invalidation was found.

## Protected State

- Do not touch `gifs/`.
- Do not change fixed evaluation protocols, WeatherBench2 splits, target
  variables, lead times, metrics, or golden usage.
- Implement exactly the selected narrow WTG envelope proposal.

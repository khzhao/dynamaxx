# Resource Snapshot

## Git And Incumbent

- Baseline commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Incumbent model: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Incumbent source: `.logbook/leaderboard.json`
- Incumbent iteration cache: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Incumbent validation cache: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Pre-existing untracked files protected from cleanup: `gifs/`

## Resources

- CPU count: `48`
- Available RAM before scoring: `171Gi`
- GPUs: `4 x NVIDIA L4`
- GPU memory before scoring: about `22566 / 23034 MiB` free on each GPU
- Disk free: `4.1T` on `/dev/root`
- Selected worker count: `4`
- Worker rationale: Four idle GPUs and more than `128Gi` available RAM support the protocol's conservative `--workers 4` setting.

## Cache Validation

- Requested incumbent matched `.logbook/leaderboard.json.incumbent_model_name`.
- Leaderboard `eval_code_commit` matched `HEAD`.
- Fixed evaluation protocols, target variables, lead range, and data path were unchanged.
- Incumbent iteration and validation artifacts existed, were readable, had finite primary scores, clean diagnostics, and complete `4 variables x 15 leads` records.
- Candidate edits were limited to dycore source, registry, and tests, so they did not invalidate the accepted incumbent cache.

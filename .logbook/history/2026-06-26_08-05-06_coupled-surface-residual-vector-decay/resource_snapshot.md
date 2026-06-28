# Resource Snapshot

- Recorded at: 2026-06-26T08:05:06Z
- Baseline commit: ff40def55ac707e8915c840b856a0aaa3345b046
- Baseline git status: candidate implementation files modified; unrelated `gifs/` untracked.
- CPU count: 48
- Available RAM: 171 GiB
- GPU count: 4
- GPU memory free: NVIDIA L4 devices 0-3 each reported 22566 MiB free of 23034 MiB total.
- Free disk for repository: 4.1 TiB
- Free disk for `outputs/eval`: 4.1 TiB
- Selected worker count for fixed iteration/validation gates: 4
- Worker rationale: the host has 171 GiB available RAM and 48 CPUs; protocol allows 4 workers under the conservative RAM policy and this stays below half the CPU count.
- Incumbent cache policy: reuse `.logbook/leaderboard.json` incumbent artifacts by default. Candidate source edits do not invalidate the accepted incumbent cache. Rerun the incumbent only if a concrete cache invalidation is documented.
- Cached incumbent iteration artifact: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Cached incumbent validation artifact: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json`

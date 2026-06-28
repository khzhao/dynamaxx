# Resource Snapshot

- Timestamp UTC: 2026-06-25T17:17:23Z
- Baseline commit: ff40def55ac707e8915c840b856a0aaa3345b046
- CPU count: 48
- Available RAM: 172 GiB
- GPUs: 4 x NVIDIA L4, each 23034 MiB total and 22566 MiB free
- Repository/output free disk: 4.1 TiB
- Selected WeatherBench2 workers: 4
- Worker rationale: four idle GPUs, available RAM above 128 GiB, and worker
  count below half of CPU cores.
- Incumbent cache status: valid and reused by default. Leaderboard incumbent
  `dino_hsl2_mass_dse_wtg_vdse_ramp` matches the requested incumbent, commit
  `ff40def55ac707e8915c840b856a0aaa3345b046` is current HEAD, iteration and
  validation artifacts exist, are readable, and contain finite primary scores.
- Pre-scoring dirty state: candidate source/test changes plus pre-existing
  untracked `gifs/`.

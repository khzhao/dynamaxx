# Resource Snapshot

- Timestamp UTC: 2026-06-25T12:52:40Z
- Baseline commit: d8561caebb78ca096263d8c412217570ff2d1f46
- CPU count: 48
- Available RAM: 172 GiB
- GPUs: 4 x NVIDIA L4, each 23034 MiB total and 22566 MiB free
- Repository/output free disk: 4.1 TiB
- Selected WeatherBench2 workers: 4
- Worker rationale: four idle GPUs, available RAM above 128 GiB, and worker
  count below half of CPU cores.
- Incumbent cache status: valid and reused by default. Leaderboard incumbent
  `dino_hsl2_mass_dse_wtg` matches the requested incumbent, commit
  `d8561caebb78ca096263d8c412217570ff2d1f46` is current HEAD, iteration and
  validation artifacts exist, are readable, and contain finite primary scores.
- Pre-scoring dirty state: candidate source/test changes plus pre-existing
  untracked `gifs/`.

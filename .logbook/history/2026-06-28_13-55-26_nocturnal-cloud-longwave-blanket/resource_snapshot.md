# Resource And Cache Snapshot

## Identity

- Proposal slug: `nocturnal-cloud-longwave-blanket`
- Candidate model name: `dino_ri2m_cloud_lw`
- Incumbent model name: `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`
- Baseline commit: `3992244f20b2a938fdd96f8904f3749f5505670d`
- Baseline git status: only pre-existing untracked `gifs/`

## Machine Resources

- CPU count: 48
- Available RAM: approximately 170 GiB
- GPU count: 4
- GPU memory: NVIDIA L4, approximately 22566 MiB free on each GPU
- Free disk: approximately 4.1 TiB on repository, evaluation output, and WeatherBench2 data paths
- Selected evaluation workers: 4
- Worker rationale: RAM exceeds 128 GiB and 4 workers is below half of available CPU cores.

## Incumbent Cache

- Leaderboard path: `.logbook/leaderboard.json`
- Incumbent commit: `3992244f20b2a938fdd96f8904f3749f5505670d`
- Iteration primary score: `-0.21299732605547173`
- Validation primary score: `-0.21274255459898536`
- Iteration artifacts:
  - `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m.json`
  - `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m.csv`
- Validation artifacts:
  - `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m.json`
  - `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m.csv`
- Cache validity: valid. Artifacts exist, are readable, have finite primary scores, contain 120 records, and match the unchanged fixed WeatherBench2 protocol fingerprint.
- Incumbent rerun policy: do not rerun the incumbent unless a concrete cache invalidation is found.

## Fixed Evaluation Policy

- Run candidate `fast` first.
- Run candidate `iteration --workers 4` only after local tests and fast diagnostics pass.
- Run candidate `validation --workers 4` only if iteration promotes by the fixed gates.
- Do not run `golden` for iterative selection.

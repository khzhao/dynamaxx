# Resource Snapshot

## Iteration Identity

- Proposal slug: `coupled-ekman-stress-pumping`
- Candidate model name: `dino_ri2m_ekman_coupled`
- Incumbent model name: `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`
- History path: `.logbook/history/2026-06-29_04-31-21_coupled-ekman-stress-pumping`
- Baseline commit: `7f4a314196fa4893939efa071bb686eda9f3669b`
- Baseline git status: tracked worktree clean; pre-existing untracked `gifs/` is user-owned and must not be touched.

## Machine Resources

- CPU count: 48
- Available RAM: 170 GiB
- GPU count: 4 NVIDIA L4 GPUs
- GPU memory: approximately 22.5 GiB free on each GPU before implementation
- Free disk: 4.1 TiB available on repository/output filesystem
- Selected evaluation workers: 4
- Worker rationale: 4 workers is within the protocol limits for 170 GiB available RAM, below half of CPU cores, and compatible with four idle L4 GPUs.

## Incumbent Cache

- Leaderboard path: `.logbook/leaderboard.json`
- Leaderboard incumbent commit: `3992244f20b2a938fdd96f8904f3749f5505670d`
- Cached iteration primary: `-0.21299732605547173`
- Cached validation primary: `-0.21274255459898536`
- Iteration artifact: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m.json`
- Validation artifact: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m.json`
- Cache validation: requested incumbent matches leaderboard, artifacts exist, primary scores are finite, each artifact has 120 records, diagnostics are clean, and candidate source edits do not invalidate the accepted incumbent cache under `roles/PROTOCOL.md`.

## Research State

- Researcher wrote two proposals.
- Evaluator moved `slantwise-symmetric-instability-adjustment` to `scrap`.
- Evaluator ranked `coupled-ekman-stress-pumping` as ready `1 of 1`.
- Orchestrator selected exactly one ready idea: `coupled-ekman-stress-pumping`.

## Fixed Protocol

- Do not change fixed WeatherBench2 protocols, metrics, target variables, data splits, or lead times.
- Do not run `golden` for iterative model selection.
- Run candidate-only fixed gates and compare to cached incumbent metrics when valid.

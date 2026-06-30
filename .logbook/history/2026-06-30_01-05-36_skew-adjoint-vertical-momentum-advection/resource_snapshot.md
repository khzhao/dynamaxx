# Resource Snapshot

## Identity

- Timestamp: 2026-06-30T01:02:21Z
- Proposal slug: skew-adjoint-vertical-momentum-advection
- Candidate model name: dino_ri2m_skewvadv
- Incumbent model name: dino_ri2m_ekman_coupled
- Baseline commit before implementation: c48695696fc0a05fd92c1020fd50a264c1cb5b59
- Accepted incumbent source commit: d187308d30a242bf38aabe5b7eb530fca522a68f
- Pre-existing worktree status: untracked `gifs/` only

## Machine Resources

- CPU count: 48
- Available RAM: approximately 170 GiB
- GPU count: 4
- GPU memory: 4 x NVIDIA L4, each 23034 MiB total and approximately 22566 MiB free
- Free disk for repository/output paths: approximately 4.1 TiB
- Selected evaluation workers: 4

## Worker Rationale

`--workers 4` follows the protocol's conservative defaults: available RAM is
above 128 GiB, CPU count is 48, GPU memory is idle, and disk space is well above
the 50 GiB minimum.

## Incumbent Cache Status

- Leaderboard incumbent metrics are present and readable.
- Iteration artifact: `outputs/eval/iteration_dino_ri2m_ekman_coupled.json`
- Validation artifact: `outputs/eval/validation_dino_ri2m_ekman_coupled.json`
- Cached iteration primary score: -0.16500618979404214
- Cached validation primary score: -0.16591150807771451
- Cached diagnostics: clean for iteration and validation
- Cache validity rationale: source and evaluation code have not changed since
  the accepted incumbent commit; later commits are logbook/leaderboard metadata
  only. Candidate source edits do not invalidate the accepted incumbent cache
  under `roles/PROTOCOL.md`.

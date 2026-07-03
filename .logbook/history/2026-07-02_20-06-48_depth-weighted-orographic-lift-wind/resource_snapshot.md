# Resource Snapshot

## Identity

- Proposal slug: depth-weighted-orographic-lift-wind
- Candidate model name: dino_ri2m_ekman_depth_orolift_lwind
- Incumbent model name: dino_ri2m_ekman_depth_orolift_theta
- Snapshot time: 2026-07-02T20:06:48Z
- HEAD: 2ced7296aeeb4433074436865395ca7b4f622500

## Repository State

- Normal `git status --short`: `?? gifs/`
- Ready proposal: `.logbook/research/ready/depth-weighted-orographic-lift-wind.md`
- Fixed evaluation protocols: unchanged
- Golden evaluation: not requested for iterative selection

## Cached Incumbent Scores

- Iteration primary score: `-0.13156559713631472`
- Validation primary score: `-0.13341144990707632`
- Cache policy: use leaderboard/cache artifacts unless concrete protocol or fingerprint invalidity is found; candidate source edits alone do not invalidate incumbent cache.

## Machine Resources

- CPU count: 48
- Available memory: approximately 169 GiB
- Disk free: approximately 4136 GiB
- GPUs: 4x NVIDIA L4, each with approximately 22566 MiB free at snapshot time

## Evaluation Plan

- Implement exactly one proposal: depth-weighted lower-column wind for orographic lift.
- Run focused tests and, if practical, `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind`.
- Run full `uv run pytest` before scorer handoff.
- Scorer should run candidate-only iteration with `--workers 4`, reuse cached incumbent scores if still valid, and skip validation unless the iteration delta clears `+0.002`.

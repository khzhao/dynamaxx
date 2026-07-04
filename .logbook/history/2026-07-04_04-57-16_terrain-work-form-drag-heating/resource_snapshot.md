# Resource Snapshot

## Iteration

- Timestamp UTC: `2026-07-04T04:57:16Z`
- Proposal slug: `terrain-work-form-drag-heating`
- Candidate model: `dino_ri2m_ekman_depth_orolift_lwind_twork_drag`
- Incumbent model: `dino_ri2m_ekman_depth_orolift_lwind`
- Baseline HEAD: `6c53d6d519dc1e092f5197558ebc099aeacfd31b`
- Accepted incumbent source commit: `db2387935aa0937eb8669de20843dc3caaccb115`
- Baseline git status: pre-existing untracked `gifs/` only

## Incumbent Cache

- Iteration primary score: `-0.1285119843716688`
- Validation primary score: `-0.12911217353049617`
- Iteration metrics JSON: `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind.json`
- Validation metrics JSON: `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind.json`
- Cache policy: reuse the leaderboard incumbent artifacts unless a concrete
  invalidation is found; candidate edits do not invalidate the accepted
  incumbent cache.

## Machine Resources

- CPU count: `48`
- Available RAM: `168 GiB`
- GPU count: `4`
- GPU memory free: four NVIDIA L4 GPUs, each with approximately `22566 MiB`
  free of `23034 MiB`
- Repository/output free disk: `4.1 TiB`
- Selected evaluation workers: `4`
- Worker rationale: resources exceed the protocol thresholds for `--workers 4`;
  this matches the recent accepted and rejected scoring runs.

## Protected State

- Pre-existing untracked path: `gifs/`
- Do not remove or modify unrelated user work.
- Fixed evaluation protocols, metrics, target variables, splits, and lead
  ranges remain unchanged.

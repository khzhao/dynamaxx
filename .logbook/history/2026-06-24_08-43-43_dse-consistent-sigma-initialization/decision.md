# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.26271419693216724`
- Iteration incumbent primary score: `-0.2616483974683927`
- Iteration delta: `-0.0010657994637745527`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.2600180396322455`
- Validation delta: not applicable

## Rationale

The candidate completed the fixed `fast` and `iteration` gates with clean
diagnostics, but it did not meet the protocol's iteration promotion threshold.
The cached incumbent iteration artifact for `dino_hsl2_mass_dse` was valid and
was reused rather than rerunning the incumbent. The candidate iteration primary
score was `-0.26271419693216724`, which is `-0.0010657994637745527` below the
incumbent score and therefore below the required `+0.002` improvement.

The guardrails were clean: early day-1-to-5 mean RMSE regression was
`-0.6345484837916622%`, and the worst variable-lead RMSE regression was
`+1.9422206593772608%` for 500 hPa geopotential at 24 hours. Because the primary
iteration gate failed, validation was skipped and golden was not run.

## Lessons Learned

- The DSE-consistent sigma initialization improved some short-lead near-surface
  and pressure behavior but slightly degraded the aggregate iteration score.
- Initialization-only DSE consistency is not sufficient to improve the current
  mass-weighted DSE-HSL incumbent under the fixed iteration metric.
- Future initialization proposals should avoid adding thermal corrections unless
  they directly target the remaining aggregate error modes identified by the
  incumbent comparison.

## Cleanup Completed

- Candidate code retained or reverted: reverted using
  `.logbook/history/2026-06-24_08-43-43_dse-consistent-sigma-initialization/candidate.diff`
- Research state updated: removed
  `.logbook/research/ready/dse-consistent-sigma-initialization.md`
- Leaderboard updated: no, rejected candidate
- Git status checked: tracked files clean; pre-existing untracked `gifs/`
  directory preserved

## Next Action

Start the next continuous-loop iteration by generating and triaging new
Researcher proposals against the cached `dino_hsl2_mass_dse` incumbent.

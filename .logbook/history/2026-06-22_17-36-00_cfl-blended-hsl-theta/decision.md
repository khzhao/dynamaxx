# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: `-1.7976931348623157e+308`
- Iteration candidate primary score: not run
- Iteration incumbent primary score: `-0.31282890543336245`
- Iteration delta: not applicable
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.3072374345999185`
- Validation delta: not applicable

## Rationale

The candidate failed the fixed fast diagnostic gate before model-selection
iteration. Both the initial linear CFL blend and the bounded square-root
CFL-weight repair produced nonfinite forecasts and nonfinite metric records.
Since the candidate could not produce finite fast metrics after a bounded repair
within the selected proposal, iteration and validation were not run.

No incumbent metrics were rerun. The leaderboard incumbent remains
`dino_hsl2_theta` at `72efada4e0afbd8e34e3184dbcef90cb91cc051c`.

## Lessons Learned

- The accepted midpoint HSL theta transport path is numerically robust, but
  pointwise Eulerian/HSL blending can destabilize the rollout.
- Future theta-transport proposals should avoid spatially varying blends with
  the pre-HSL Eulerian tendency unless they include a stronger stability
  argument and a local finite-state fallback.

## Cleanup Completed

- Candidate code retained or reverted: reverted from `candidate.diff`.
- Research state updated: selected ready proposal removed after rejection.
- Leaderboard updated: no, rejected candidates do not update the incumbent.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Continue the optimization loop with incumbent `dino_hsl2_theta` and generate or
triage the next ready idea.

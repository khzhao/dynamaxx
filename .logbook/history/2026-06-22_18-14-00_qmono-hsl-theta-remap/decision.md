# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.3714466304069767`
- Iteration incumbent primary score: `-0.31282890543336245`
- Iteration delta: `-0.05861772497361423`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.3072374345999185` from cached
  leaderboard artifacts, not used for this decision
- Validation delta: not applicable

## Rationale

`dino_hsl_qmono` passed the fast gate with clean diagnostics, but it failed the
fixed iteration promotion gate. The primary score delta was
`-0.05861772497361423`, below the required `+0.002` improvement threshold, so
validation was correctly skipped.

The guardrails reinforced the rejection. Early day 1 to 5 mean RMSE regressed
by up to `+4.741512494129507%`, above the 2% early-lead limit. The worst
variable-lead RMSE regression was `+8.41085767071934%` for mean sea-level
pressure at lead hour 360, below the 10% worst-lead limit but still unfavorable.
Diagnostics were clean, so this is a scientific/numerical regression rather
than an infrastructure failure.

Incumbent comparison used the valid leaderboard cache for `dino_hsl2_theta`;
the incumbent was not rerun.

## Lessons Learned

- Replacing bilinear theta-anomaly remapping with a bounded qmono remap reduces
  neither the fixed primary error nor early-lead RMSE for the accepted HSL2
  theta path.
- The added higher-order remap is computationally expensive in the fixed
  iteration protocol, completing much more slowly than the incumbent path.
- Future HSL-theta proposals should target departure geometry, layer coherence,
  or transport-variable choice rather than increasing interpolation order at
  the accepted departure point.

## Cleanup Completed

- Candidate code retained or reverted: source and test changes were reverted
  from `candidate.diff`.
- Research state updated: ready proposal will be removed from
  `.logbook/research/ready`.
- Leaderboard updated: no. The incumbent remains `dino_hsl2_theta`.
- Git status checked: clean tracked worktree after rollback.

## Next Action

Rollback `dino_hsl_qmono`, leave the tracked worktree clean, then continue the
optimization loop with the next evaluated ready proposal or request new
research proposals if the ready queue is empty.

# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: `-Infinity`
- Iteration candidate primary score: not run
- Iteration incumbent primary score: `-0.31282890543336245`
- Iteration delta: not applicable
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.3072374345999185`
- Validation delta: not applicable

## Rationale

`dino_hsl2_theta_cpvert` failed the fixed fast gate. The initial fast run
produced nonfinite forecasts and nonfinite metrics at all candidate lead rows.
A bounded repair was attempted inside the selected proposal: overlarge finite
Charney-Phillips/interface theta vertical tendencies fall back to the accepted
centered vertical theta tendency. After repair, local tests passed, but fast
still failed with nonfinite forecasts and metrics from 48 hours onward.

Because the candidate did not pass fast, iteration and validation were not run.
No incumbent evaluation was rerun. Cached incumbent iteration and validation
artifacts were checked and remained valid, but no candidate comparison was
possible beyond the fast-gate failure.

## Lessons Learned

- Interface-sampled theta vertical transport is unstable in this implementation
  family even with finite fallback and a bounded local tendency guard.
- The first nonfinite fast metrics appear after the 24-hour lead, so the failure
  is a forecast-stability issue rather than a registration, local-test, or
  immediate shape bug.
- Future vertical theta proposals should use a more conservative stability
  argument than interface flux reconstruction alone, or first add diagnostics
  that localize vertical tendency blow-up before changing the model-selection
  path.

## Cleanup Completed

- Candidate code retained or reverted: reverted after saving `candidate.diff`.
- Research state updated: ready proposal removed after terminal decision.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: yes, after rollback.

## Next Action

Continue the optimization loop with a fresh Researcher/Evaluator pass or a new
triage of staged ideas, selecting exactly one ready proposal.

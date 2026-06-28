# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.31282890543336245`
- Iteration incumbent primary score: `-0.32000443139324114`
- Iteration delta: `+0.0071755259598786925`
- Validation candidate primary score: `-0.3072374345999185`
- Validation incumbent primary score: `-0.31443387067049233`
- Validation delta: `+0.007196436070573853`

## Rationale

The candidate passed all fixed model-selection gates against cached
`dino_hsl_theta` incumbent artifacts. Incumbent iteration and validation metrics
were reused from valid leaderboard cache artifacts; no incumbent evaluation was
rerun.

Fast diagnostics were clean. Iteration exceeded the `+0.002` promotion
threshold, and validation exceeded the `+0.001` acceptance threshold.
Diagnostics were clean for fast, iteration, and validation. Early day 1-5 mean
RMSE guardrails passed for every target variable. No per-variable/lead RMSE
regression exceeded the 10% guardrail; the worst reported regressions were
about `+0.0193%` on iteration and `+0.0218%` on validation for
`10m_u_component_of_wind` at 24 hours.

The implementation is side-by-side under `dino_hsl2_theta`, keeps the forecast
contract unchanged, and changes only the horizontal dry-theta anomaly departure
estimate for the accepted semi-Lagrangian theta transport path. The accepted
first-order `dino_hsl_theta` path remains the fallback for invalid midpoint
diagnostics.

## Lessons Learned

- Midpoint trajectory estimation adds measurable value on top of the accepted
  first-order horizontal semi-Lagrangian theta transport.
- The fixed eval artifacts include persistence rows, so scorer guardrails must
  continue filtering rows by model name.
- Incumbent cache reuse worked as intended: candidate source edits did not
  trigger a redundant incumbent run.
- Accepted dycore commits must include the full positive-commit protocol body:
  proposal, model, iteration delta, validation delta, and main files changed.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as
  `72efada4e0afbd8e34e3184dbcef90cb91cc051c`.
- Research state updated: selected ready proposal removed after acceptance.
- Leaderboard updated: yes, to `dino_hsl2_theta` and its fixed eval artifact
  paths.
- Git status checked: tracked worktree clean after commit.

## Next Action

Start the next continuous-loop iteration immediately.

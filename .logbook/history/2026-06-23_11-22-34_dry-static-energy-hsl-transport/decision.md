# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.26737373217433574`
- Iteration incumbent primary score: `-0.31282890543336245`
- Iteration delta: `+0.045455173259026704`
- Validation candidate primary score: `-0.2654819769882763`
- Validation incumbent primary score: `-0.3072374345999185`
- Validation delta: `+0.04175545761164218`

## Rationale

The candidate passed all fixed model-selection gates against cached
`dino_hsl2_theta` incumbent artifacts. The incumbent matched the leaderboard
incumbent, the cached iteration and validation artifacts were readable and
compatible with the current fixed protocol fingerprint, and no incumbent
evaluation was rerun.

Fast, iteration, and validation diagnostics were clean. Iteration exceeded the
`+0.002` promotion threshold, and validation exceeded the `+0.001` acceptance
threshold. Early day 1-5 mean RMSE guardrails passed for every target variable
on both iteration and validation. No per-variable/lead RMSE regression violated
the 10% guardrail; the reported worst variable/lead changes were improvements
of about `-0.0626%` on iteration and `-0.0613%` on validation for
`10m_u_component_of_wind` at 24 hours.

The implementation is side-by-side under `dino_hsl2_theta_dse_hsl`, keeps the
forecast contract unchanged, and only changes the optional thermodynamic
transport variable for the accepted HSL2 theta path. Invalid dry-static-energy
diagnostics fall back to the accepted theta-HSL tendency.

## Lessons Learned

- Transporting dry static energy with the accepted HSL2 departure produced
  broad RMSE improvements across iteration and validation.
- The validation delta stayed close to the iteration delta, which did not show
  an obvious validation-only overfit signal.
- Incumbent cache reuse worked as intended: candidate source edits did not
  trigger a redundant incumbent run.
- Accepted dycore commits must include the full positive-commit protocol body:
  proposal, model, iteration delta, validation delta, and main files changed.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as
  `a274541cc57f593b8e5796e1df8307e8820c2d6b`.
- Research state updated: selected ready proposal removed after acceptance.
- Leaderboard updated: yes, to `dino_hsl2_theta_dse_hsl` and its fixed eval
  artifact paths.
- Git status checked: tracked worktree clean after commit.

## Next Action

Start the next continuous-loop iteration immediately.

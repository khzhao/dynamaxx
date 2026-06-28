# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.3128289740179898`
- Iteration incumbent primary score: `-0.31282890543336245`
- Iteration delta: `-0.0000000685846273662527`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.3072374345999185`
- Validation delta: not run

## Rationale

`dino_hsl2_theta_pw_ramp` passed unit tests, fast scoring, and iteration
diagnostics. It did not promote because its iteration primary delta was
`-6.85846273662527e-08`, below the required `+0.002` threshold. Validation was
therefore skipped.

The RMSE guardrails passed. Early day-1-to-5 mean RMSE regressions were
negligible, and the worst single variable-and-lead RMSE regression was
`2m_temperature` at day 11 with `+2.761361805880824e-07%`, far below the
`10%` limit. This candidate was stable but effectively neutral, so it did not
justify validation compute.

The incumbent `dino_hsl2_theta` comparison used the compatible cached
leaderboard artifacts; no incumbent rerun was performed.

## Lessons Learned

- The conservative ramp, column-neutral projection, and cap removed the
  short-lead MSLP/Z500 damage seen in the unconstrained pressure-work candidate,
  but also removed the measurable primary-score gain.
- The large pressure-work signal appears tied to the same mass/thickness
  response that the fixed guardrails rejected.
- Further pressure-work variants need a stronger physically balanced operator,
  not just post hoc damping of the added increment.

## Cleanup Completed

- Candidate code retained or reverted: reverted with
  `.logbook/history/2026-06-23_08-53-50_ramped-column-neutral-theta-pressure-work/candidate.diff`.
- Research state updated: removed
  `.logbook/research/ready/ramped-column-neutral-theta-pressure-work.md`; copied
  immutable proposal remains in this history directory.
- Leaderboard updated: no, rejected candidate did not replace the incumbent.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Continue the open-ended optimization loop with a new Researcher/Evaluator
iteration. Future pressure-work proposals should avoid simple amplitude/ramp
constraints unless they introduce a stronger balance-preserving discretization.

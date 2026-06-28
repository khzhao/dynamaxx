# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.22517062459723133`
- Iteration incumbent primary score: `-0.31282890543336245`
- Iteration delta: `+0.08765828083613111`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.3072374345999185`
- Validation delta: not run

## Rationale

`dino_hsl2_theta_pw` passed unit tests, fast scoring, and iteration diagnostics,
and its iteration primary delta cleared the `+0.002` threshold. It did not
promote because both fixed iteration guardrails failed:

- `geopotential_500` day-1-to-5 mean RMSE regressed by `+2.409417583035754%`,
  above the `2%` limit.
- The worst variable-and-lead RMSE regression was
  `mean_sea_level_pressure` at 24h with `+26.501130746134606%`, above the
  `10%` limit. `geopotential_500` at 24h also regressed by
  `+13.193213219084956%`.

Validation was skipped because iteration did not promote. The incumbent
`dino_hsl2_theta` comparison used the compatible cached leaderboard artifacts;
no incumbent rerun was performed.

A bounded revision was not requested in this implementation state because the
natural mitigation is a pressure-work limiter or balance cap, which is a
separate model idea already represented in research staging. Revising this
candidate in place would mix a new limiter experiment into the selected
hydrostatic pressure-work proposal after seeing iteration guardrail failures.

## Lessons Learned

- Hydrostatic theta pressure-work can improve the aggregate iteration score
  substantially while damaging short-lead mass and thickness fields.
- Future pressure-work variants should constrain short-lead pressure and
  geopotential balance before validation compute is spent.
- Guardrail calculations must filter metric rows by model name because the raw
  metric files include persistence reference rows.

## Cleanup Completed

- Candidate code retained or reverted: reverted with
  `.logbook/history/2026-06-23_03-46-01_hydrostatic-balanced-theta-pressure-work/candidate.diff`.
- Research state updated: removed
  `.logbook/research/ready/hydrostatic-balanced-theta-pressure-work.md`; copied
  immutable proposal remains in this history directory.
- Leaderboard updated: no, rejected candidate did not replace the incumbent.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Continue the open-ended optimization loop with a new Researcher/Evaluator
iteration. The next proposal should account for the short-lead MSLP and Z500
guardrail failures observed here.

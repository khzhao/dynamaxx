# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.1652580985873155`
- Iteration incumbent primary score: `-0.16500618979404214`
- Iteration delta: `-0.0002519087932733588`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.16591150807771451`
- Validation delta: not applicable

## Rationale

The candidate `dino_ri2m_ekman_tcenter` completed the fixed fast and iteration
gates without diagnostic failures. The iteration candidate primary score
regressed by `-0.0002519087932733588` against the cached incumbent
`dino_ri2m_ekman_coupled` score from `.logbook/leaderboard.json`.

The iteration gate requires a primary delta of at least `+0.002` before
validation. Because the candidate did not clear that gate, validation was
skipped and the candidate cannot be accepted. The incumbent iteration and
validation artifacts were checked and reused from the leaderboard cache; no
incumbent rerun was performed.

Iteration guardrails were clean after filtering to evaluated-model rows only:
no early-lead mean RMSE regression exceeded 2 percent and no single
variable-lead RMSE regression exceeded 10 percent. The rejection is driven by
the primary-score regression, not by numerical instability.

## Lessons Learned

- Time-centering the coupled Ekman source diagnostics is stable, but it slightly
  weakens the incumbent coupled Ekman WeatherBench2 iteration score.
- The accepted endpoint closure should remain the incumbent path for now.
- Future scoring checks should continue filtering evaluated-model rows by model
  name because evaluation artifacts also contain persistence rows.

## Cleanup Completed

- Candidate code retained or reverted: reverted with
  `.logbook/history/2026-06-30_13-44-26_time-centered-ekman-stress-pumping/candidate.diff`.
- Research state updated: proposal moved into immutable history; the unrelated
  `snow-albedo-shortwave-shield` idea remains staged for possible future
  triage.
- Leaderboard updated: no; rejected candidates do not update the incumbent.
- Git status checked: `git status --short` showed only pre-existing `?? gifs/`
  after rollback.

## Next Action

Continue the open-ended optimization loop by starting the next iteration from
the cached incumbent `dino_ri2m_ekman_coupled`.

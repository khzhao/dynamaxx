# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: -1.0905432571118128
- Fast diagnostics: passed, issue count 0
- Iteration candidate primary score: -1.122351043157642
- Iteration incumbent primary score: -1.3208025947740873
- Iteration delta: +0.19845155161644534
- Validation candidate primary score: -1.126083021438326, anomalous extra measurement
- Validation incumbent primary score: -1.308334010223954
- Validation delta: +0.18225098878562807, not protocol-eligible

## Rationale

The candidate passed fixed diagnostics and substantially improved the aggregate primary score, but it failed the fixed RMSE guardrails that are required for promotion. On iteration, early lead 1-5 mean RMSE regressed by `+36.02191018071786%` for `geopotential_500` and `+32.23194296316327%` for `mean_sea_level_pressure`, and 8 target variable/lead RMSE regressions exceeded the 10% guardrail. The largest iteration regression was `geopotential_500` day 1 at `+209.05849934783322%`.

Validation was run by the Scorer after a parsing mistake, but the corrected iteration gate did not permit validation. The validation artifact is retained as an anomaly and shows the same guardrail failure pattern, not acceptance evidence. Under the protocol, this candidate must be rejected and rolled back.

## Lessons Learned

- Terrain and MSLP handling can improve the aggregate skill-vs-persistence primary score while damaging early absolute mass-field RMSE beyond acceptable guardrails.
- Primary-score gains must not override fixed guardrails; for terrain experiments, early Z500 and MSLP RMSE must be inspected before validation.
- A future terrain proposal would need a separate, narrower infrastructure or diagnostic design that avoids conflating terrain geopotential, surface-pressure diagnosis, and MSLP reduction in one model-selection candidate.

## Cleanup Completed

- Candidate code retained or reverted: reverted; no candidate code retained in tracked source/test files.
- Research state updated: removed from `.logbook/research/ready`; immutable copy retained in this history directory.
- Leaderboard updated: no; incumbent remains `dinosaur_dfi`.
- Git status checked: clean tracked worktree after rollback.

## Next Action

Continue the loop by re-triaging the remaining staged ideas against the accepted `dinosaur_dfi` incumbent. Do not run `golden`.

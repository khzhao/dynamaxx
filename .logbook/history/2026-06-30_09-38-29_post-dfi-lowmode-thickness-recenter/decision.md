# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.16500616889205458
- Iteration incumbent primary score: -0.16500618979404214
- Iteration delta: +0.000000020901987557442325
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.16591150807771451
- Validation delta: not available

## Rationale

The candidate passed the fast sanity gate and iteration diagnostics, but it did not meet the fixed promotion threshold. The iteration primary-score delta was only `+2.0901987557442325e-08`, far below the required `+0.002` improvement over the cached incumbent. This is numerical-noise scale, not a meaningful WeatherBench2 gain.

Iteration guardrails were clean: diagnostics reported `failed=false` and `issues=0`; all 1-5 day mean RMSE regressions were far below the 2% threshold; the largest single variable/lead RMSE regression was `+3.0598054432752663e-07` for `2m_temperature` at day 15, far below the 10% guardrail. Because the promotion gate failed, validation was correctly skipped and the golden protocol was not run.

The incumbent was not rerun. The Scorer validated and reused the leaderboard artifacts for `dino_ri2m_ekman_coupled`, including `outputs/eval/iteration_dino_ri2m_ekman_coupled.json` and `outputs/eval/validation_dino_ri2m_ekman_coupled.json`, under the cache policy in `roles/PROTOCOL.md` and `roles/SCORER.md`.

## Lessons Learned

- Post-DFI low-mode hydrostatic thickness recentering is effectively neutral relative to the accepted Ekman-coupled incumbent.
- The strict correction guards kept diagnostics and RMSE guardrails clean, but the correction did not move the aggregate score enough to justify validation compute.
- Future initialization proposals should target a more directly observable remaining error source or include stronger evidence that the accepted DFI state retains a material correctable imbalance.

## Cleanup Completed

- Candidate code retained or reverted: reverted after recording `candidate.diff`.
- Research state updated: selected proposal moved to this history directory; paired scrapped proposal remains in research scrap.
- Leaderboard updated: no. The incumbent remains `dino_ri2m_ekman_coupled`.
- Git status checked: pending final rollback and metadata commit at the time this decision file was written.

## Next Action

Start the next continuous-loop iteration after rollback, metadata commit, and clean worktree verification.

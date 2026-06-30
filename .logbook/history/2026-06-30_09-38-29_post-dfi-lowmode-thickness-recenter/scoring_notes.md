# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_ri2m_postdfi_thick` exited 0, diagnostics failed=False, issues=0, primary=-0.1677176844579508.
- Iteration promotion gate: did not pass. Candidate iteration primary=-0.16500616889205458 versus cached incumbent iteration primary=-0.16500618979404214, delta=+2.0901987557442325e-08, below the required +0.002 threshold.
- Iteration diagnostics and RMSE guardrails were clean: diagnostics failed=False, issues=0; all 1-5 day mean RMSE regressions were far below 2%; the largest single variable/lead RMSE regression was +3.0598054432752663e-07 for 2m_temperature at day 15, far below 10%.
- Validation acceptance gate: not evaluated. Candidate validation was skipped because the iteration promotion gate did not pass. Golden was not run.

## Cache Validation

- Incumbent metrics were reused from `.logbook/leaderboard.json`; the incumbent was not rerun.
- Requested incumbent `dino_ri2m_ekman_coupled` matched the leaderboard incumbent.
- Cached iteration artifact `outputs/eval/iteration_dino_ri2m_ekman_coupled.json` was present, readable, finite, contained incumbent rows, and contained records needed for guardrail comparisons.
- Cached validation artifact `outputs/eval/validation_dino_ri2m_ekman_coupled.json` was present, readable, finite, contained incumbent rows, and remained cache-valid, but was not used for a candidate validation delta because validation was skipped.
- Leaderboard fingerprint matched the fixed evaluation setup: data path, target variables, lead days, and protocol coverage were compatible.
- Current `HEAD` was `399e133aa14b83cd8fd3dd16f48d267df8a84bf5`, while the leaderboard eval code commit was `d187308d30a242bf38aabe5b7eb530fca522a68f`. `git diff --name-only d187308d30a242bf38aabe5b7eb530fca522a68f -- src/dynamaxx/eval src/dynamaxx/cli.py src/dynamaxx/data src/dynamaxx/utils/consts.py` was empty, so the fixed eval/data code used for scoring was unchanged. Candidate dycore edits do not invalidate the accepted incumbent cache under `roles/PROTOCOL.md`.

## Anomalies

- Resource limits: no resource failure observed. Iteration completed with 4 workers on the 4 available GPUs.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by fast or iteration diagnostics.
- Incumbent recomputation: none. Cached incumbent iteration and validation artifacts were reused/validated according to policy; no incumbent eval command was run.

## Measurement Lessons

- The candidate was effectively metric-neutral relative to the incumbent on iteration: the primary-score gain was only +2.0901987557442325e-08.
- RMSE differences were at numerical-noise scale and did not identify a guardrail regression, but the aggregate primary score did not support spending validation compute on this implementation state.

## Recommendation To Orchestrator

Use these measurements for the decision step. The Scorer does not accept or reject the candidate.

# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate fast completed with `failed=False`, 0 diagnostic issues, 120 records, and primary score `-0.31552298407281926`.
- Iteration promotion gate: did not pass. Candidate iteration primary score `-0.3128289740179898` versus cached incumbent `-0.31282890543336245` gives delta `-6.85846273662527e-08`, below the required `+0.002`. Candidate diagnostics were clean. Early day 1-5 mean RMSE regressions all passed the `<= 2%` guardrail. Worst variable+lead RMSE regression was `2.76136180588e-07%` for `2m_temperature` at lead day `11.0`, passing the `<= 10%` guardrail.
- Validation acceptance gate: not evaluated. Validation was permitted only after iteration promotion, and the candidate did not promote. Golden was not run.

## Measurement Lessons

- The ramped pressure-work candidate is numerically stable under fast and iteration diagnostics, but its iteration score is effectively tied with the incumbent and slightly lower by `-6.85846273662527e-08`. The added mechanism did not produce a measurable model-selection gain on the fixed iteration protocol.
- Guardrail regressions were negligible, so the non-promotion was driven by primary score rather than localized RMSE degradation.

## Anomalies

- Cache reuse: reused `.logbook/leaderboard.json` incumbent pointers for iteration and validation artifacts. Checks confirmed requested incumbent `dino_hsl2_theta`, current HEAD and leaderboard incumbent commit `72efada4e0afbd8e34e3184dbcef90cb91cc051c`, readable artifacts, finite primary scores, 120 records, required target variables, and lead days 1..15. Candidate source edits were not treated as incumbent-cache invalidation under protocol.
- Resource limits: no resource failure observed. Iteration used the requested `--workers 4`; evaluator reported GPU dispatch with 4 effective workers.
- Failed or restarted commands: one preliminary registration check failed because it imported a non-existent helper (`get_model_factory`). The corrected `DYCORE_MODEL_FACTORIES` registration check passed before any evaluation command ran. No evaluation command failed or was restarted.
- Nonfinite or unstable outputs: none observed; fast and iteration diagnostics had 0 issues.

## Recommendation To Orchestrator

Report that `dino_hsl2_theta_pw_ramp` completed fast and iteration cleanly but did not meet the iteration promotion threshold, so validation was correctly skipped. The measured result supports moving to the Orchestrator decision step without accepting or rejecting in this Scorer note.

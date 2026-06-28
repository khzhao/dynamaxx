# Scoring Notes

## Gate Status

- Fast gate: candidate command completed with exit status 0; diagnostics failed=false, issue_count=0, primary_score=-0.32243765258030105.
- Iteration promotion gate: candidate primary_score=-0.32000443139324114, cached incumbent primary_score=-0.42701187536092744, delta=0.1070074439676863; threshold +0.002 was exceeded. Candidate diagnostics were clean. Maximum day 1-5 mean RMSE regression was -3.56182799295% for geopotential_500; worst variable+lead RMSE regression was -0.319372621809% for geopotential_500 at day 1. The measured numeric/diagnostic promotion gate passed.
- Validation acceptance gate metrics: candidate primary_score=-0.31443387067049233, cached incumbent primary_score=-0.417391902036791, delta=0.10295803136629866; threshold +0.001 was exceeded. Candidate diagnostics were clean. Maximum day 1-5 mean RMSE regression was -3.28282629959% for geopotential_500; worst variable+lead RMSE regression was -0.288614969521% for geopotential_500 at day 1. The measured numeric/diagnostic validation gate passed.

## Cache Reuse

- Incumbent iteration metrics were reused from leaderboard artifacts: outputs/eval/iteration_ocean_bulk_sensible_heat_flux.json and outputs/eval/iteration_ocean_bulk_sensible_heat_flux.csv. The requested incumbent matched `.logbook/leaderboard.json`, the fingerprint matched data path, target variables, lead_days, protocols, and eval_code_commit=329dd5758204b7e77f1abb258b1dab9ee5d9b2c8, and the artifact contained finite primary score plus all required incumbent guardrail rows. No incumbent iteration rerun was performed.
- Incumbent validation metrics were reused from leaderboard artifacts: outputs/eval/validation_ocean_bulk_sensible_heat_flux.json and outputs/eval/validation_ocean_bulk_sensible_heat_flux.csv. The same leaderboard/fingerprint/readability/finite-score/guardrail-row checks passed. No incumbent validation rerun was performed.

## Measurement Lessons

- The candidate improved primary score substantially on both iteration and validation while also reducing RMSE versus the incumbent on every reported variable+lead guardrail comparison.
- Metrics files include persistence baseline rows as well as evaluated-model rows, so scorer calculations must filter records by `model_name` before computing RMSE guardrails.

## Anomalies

- Cache reuse: no cache invalidation was found; incumbent artifacts were reused for iteration and validation.
- Resource limits: none observed.
- Failed or restarted commands: none. The user interrupted the interactive turn after validation had started; the existing candidate validation process was reattached and finished successfully, with no duplicate validation launch.
- Nonfinite or unstable outputs: none reported by diagnostics.

## Recommendation To Orchestrator

Proceed to the decision phase using these measured gate results. This Scorer report does not accept or reject the candidate.

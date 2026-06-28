# Scoring Notes

## Gate Status

- Fast gate: passed using the pre-existing authorized fast artifact. Candidate fast primary_score=-0.8005260563594255, failed=False, issues=0, records=120.
- Registration gate: passed. Both the candidate and incumbent were listed by `dycore_model_names()` and constructible with `create_dycore_model()` as `DinosaurPrimitiveEquationsDycoreModel`.
- Iteration promotion gate: passed. Candidate primary_score=-0.8348806410796545; incumbent primary_score=-0.8503285831632285; iteration_delta=+0.015447942083573918, above the +0.002 threshold. Candidate and incumbent diagnostics were clean.
- Iteration early day 1-5 mean RMSE guard: passed. Overall early mean RMSE relative change was +0.5350022340658391%, below the +2% threshold. By variable, 2m_temperature improved by -1.4928768134253747%, 10m_u_component_of_wind improved by -0.9030350919406513%, geopotential_500 regressed by +0.7100948329013904%, and mean_sea_level_pressure regressed by +0.42732980713397595%.
- Iteration variable+lead RMSE guard: passed. No variable+lead exceeded the +10% regression threshold; the largest positive variable+lead change was mean_sea_level_pressure day 1 at +1.7579965544157576%.
- Validation acceptance gate: passed by measurement. Candidate primary_score=-0.8200230307466544; incumbent primary_score=-0.8392576077353403; validation_delta=+0.019234576988685914, above the +0.001 threshold. Candidate and incumbent diagnostics were clean.
- Validation early day 1-5 mean RMSE guard: passed. Overall early mean RMSE relative change was +0.15635222687726263%, below +2%. By variable, 2m_temperature improved by -1.5414271395644157%, 10m_u_component_of_wind improved by -1.084760850514485%, mean_sea_level_pressure improved by -0.02040211103200278%, and geopotential_500 regressed by +0.41948562554497304%.
- Validation variable+lead RMSE guard: passed. No variable+lead exceeded +10%; the largest positive variable+lead change was mean_sea_level_pressure day 1 at +1.6361908236509046%.

## Measurement Lessons

- The candidate improved primary score on both fixed splits: +0.015447942083573918 on iteration and +0.019234576988685914 on validation.
- The clearest RMSE improvement was in 2m_temperature at day 9: -2.1851705784152813% on iteration and -2.3586769437691917% on validation.
- The main measurable regression was day-1 mean_sea_level_pressure RMSE, but it remained well inside the +10% variable+lead guardrail and early day 1-5 aggregate regressions stayed below +2%.
- Compared with the incumbent, the theta-tendency change appears to trade small early pressure/geopotential degradation for larger temperature and wind gains while passing the fixed gates.

## Anomalies

- Cache reuse: candidate focused pytest, full pytest, and fast records were reused from the Implementer record as authorized. Compatible incumbent iteration and validation artifacts were reused from `.logbook/leaderboard.json`. Candidate iteration and validation both reported cached=0 at startup.
- Resource limits: none observed. Iteration used 229 chunks with 4 effective GPU workers; validation used 46 chunks with 4 effective GPU workers.
- Failed or restarted commands: two non-gate exploratory registration probes failed because this repository exposes `dycore_model_names()`, not `list_dycore_models()` or `list_models()`. The corrected registration and constructibility checks exited 0.
- Nonfinite or unstable outputs: none reported. Candidate fast, iteration, and validation diagnostics all had failed=False and issue_count=0.

## Recommendation To Orchestrator

Report the measured gate status only: fast passed, iteration promoted to validation, validation acceptance gates passed by measurement, and golden was not run. The Scorer does not accept or reject the candidate.

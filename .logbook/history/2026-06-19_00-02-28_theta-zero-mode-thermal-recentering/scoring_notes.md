# Scoring Notes

## Gate Status

- Fast gate: passed using the pre-existing authorized fast artifact. Candidate fast primary_score=-0.7992299367936251, failed=False, issues=0, records=120.
- Registration gate: passed after correcting the helper name to `create_dycore_model()`. Both the candidate and incumbent were constructible as `DinosaurPrimitiveEquationsDycoreModel`.
- Iteration promotion gate: passed by measurement. Candidate primary_score=-0.8308832822743712; incumbent primary_score=-0.8348806410796545; iteration_delta=0.003997358805283291, above the +0.002 threshold. Candidate and incumbent diagnostics were clean.
- Iteration early day 1-5 mean RMSE guard: passed. Overall early mean RMSE relative change was -0.049012852833619176%, below the +2% threshold. By variable, 10m_u_component_of_wind changed by 0.9135235634551446%, 2m_temperature changed by -2.037876429275163%, geopotential_500 changed by -0.1603839008981452%, and mean_sea_level_pressure changed by 0.041828212296766365%.
- Iteration variable+lead RMSE guard: passed. No variable+lead exceeded the +10% regression threshold; the largest positive variable+lead change was 10m_u_component_of_wind day 15.0 at 8.010338959282189%.
- Validation acceptance gate: passed by measurement only. Candidate primary_score=-0.8148379476593253; incumbent primary_score=-0.8200230307466544; validation_delta=0.005185083087329123, above the +0.001 threshold. Candidate and incumbent diagnostics were clean.
- Validation early day 1-5 mean RMSE guard: passed. Overall early mean RMSE relative change was -0.050326924901449965%, below the +2% threshold. By variable, 10m_u_component_of_wind changed by 0.8087150169577809%, 2m_temperature changed by -1.894066510467805%, geopotential_500 changed by -0.15993347704938876%, and mean_sea_level_pressure changed by 0.03991504008961197%.
- Validation variable+lead RMSE guard: passed. No variable+lead exceeded the +10% regression threshold; the largest positive variable+lead change was 10m_u_component_of_wind day 15.0 at 7.039021793195873%.
- Golden: not run, as required for iterative model selection.

## Measurement Lessons

- The theta zero-mode thermal recentering candidate improved the fixed iteration primary score by 0.003997358805283291 and the fixed validation primary score by 0.005185083087329123 relative to the current theta-tendency incumbent.
- The largest RMSE regressions were concentrated in late 10m_u_component_of_wind: iteration day 15.0 at 8.010338959282189% and validation day 15.0 at 7.039021793195873%, both under the +10% guardrail.
- Early aggregate RMSE improved slightly on both protocols: iteration -0.049012852833619176% and validation -0.050326924901449965%.
- The largest variable+lead improvements were 2m_temperature day 9.0 on iteration at -3.141013788770915% and day 9.0 on validation at -2.9479301346896962%.
- Future thermal-recentering proposals should account for the late-wind tradeoff, because the Richardson 10 m diagnostic kept early wind within guardrail but late 10m_u_component_of_wind remained the limiting regression.

## Anomalies

- Cache reuse: candidate focused pytest, full pytest, and fast records were reused from the Implementer record as authorized. Compatible incumbent iteration and validation artifacts were reused from `.logbook/leaderboard.json`.
- Registration precheck: one preliminary helper-name check tried to import `get_model` from `dynamaxx.dycore.registry` and exited 1. The correct `create_dycore_model()` registration check passed, and no files were modified by that failed precheck.
- Resource limits: none observed. Iteration used 229 chunks with 4 effective GPU workers; validation used 46 chunks with 4 effective GPU workers; CPU count was 48, available RAM was about 174 GiB, and four L4 GPUs each reported 22566 MiB free in the resource check.
- Nonfinite or unstable outputs: none reported. Candidate fast, iteration, and validation diagnostics had failed=False and issue_count=0.
- Protocol limits: golden was not run; source code, tests, roles, evaluation protocols, metrics, target variables, data splits, lead times, and leaderboard were not changed by Scorer.

## Recommendation To Orchestrator

Report measured gate status only: fast passed, iteration promoted to validation, validation passed the measurement thresholds, and golden was not run. The Scorer does not accept or reject the candidate.

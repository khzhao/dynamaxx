# Scoring Notes

## Gate Status

- Fast gate: passed using the pre-existing authorized fast artifact. Candidate fast primary_score=-0.5579053092066798, failed=False, issues=0, records=120.
- Registration gate: passed after correcting the helper name to `create_dycore_model()`. Both candidate and incumbent were registered and constructible as `DinosaurPrimitiveEquationsDycoreModel`.
- Iteration promotion gate: passed by measurement. Candidate primary_score=-0.5719873627530224; incumbent primary_score=-0.8309027246148776; iteration_delta=+0.258915361861855, above the +0.002 threshold. Candidate and incumbent diagnostics were clean.
- Iteration early day 1-5 mean RMSE guard: passed. Overall early mean RMSE relative change was -13.552350%, below the +2.0% threshold. By variable: 10m_u_component_of_wind -5.312530%, 2m_temperature -0.769539%, geopotential_500 -13.239031%, mean_sea_level_pressure -13.908521%.
- Iteration variable+lead RMSE guard: passed. No variable+lead exceeded the +10.0% regression threshold; the largest positive variable+lead change was 2m_temperature day 15.0 at +3.789818%.
- Validation acceptance gate: passed by measurement only. Candidate primary_score=-0.562579968224105; incumbent primary_score=-0.8148384940015672; validation_delta=+0.252258525777462, above the +0.001 threshold. Candidate and incumbent diagnostics were clean.
- Validation early day 1-5 mean RMSE guard: passed. Overall early mean RMSE relative change was -13.031783%, below the +2.0% threshold. By variable: 10m_u_component_of_wind -5.162341%, 2m_temperature -0.885546%, geopotential_500 -12.590869%, mean_sea_level_pressure -13.483251%.
- Validation variable+lead RMSE guard: passed. No variable+lead exceeded the +10.0% regression threshold; the largest positive variable+lead change was 2m_temperature day 15.0 at +3.583942%.
- Golden: not run, as required.

## Measurement Lessons

- Off-centered SIL3 produced a large primary-score gain over the current-source incumbent on both fixed scored protocols: iteration +0.258915361861855 and validation +0.252258525777462.
- The strongest RMSE improvements were late-lead mass-field improvements. Iteration max improvement was mean_sea_level_pressure day 15.0 at -39.198532%; validation max improvement was mean_sea_level_pressure day 15.0 at -39.106921%.
- The remaining guardrail cost is modest late `2m_temperature` RMSE, not mass-field instability: iteration max positive variable+lead change +3.789818% and validation max positive variable+lead change +3.583942%.
- For future in-place dycore experiments, rerunning the incumbent command is not enough if the eval harness reports cached chunks. Use `--restart` or prove the cache keys include the modified source state.

## Anomalies

- Cache reuse: candidate focused pytest, full pytest, `git diff --check`, and fast records were reused from the Implementer verification as authorized. Candidate iteration and validation were freshly run.
- Incumbent cache reuse: leaderboard incumbent iteration and validation artifacts were explicitly rejected because shared time-integration source `src/dynamaxx/dycore/models/dinosaur/time_integration.py` was modified in-place for the experiment, and the incumbent imports and calls that source. Incumbent iteration and validation were recomputed with `--restart`.
- Eval chunk cache: the first incumbent iteration command without `--restart` exited 0 but reported `cached=229` and `pending=0`; it was superseded and not used for scoring. Final incumbent iteration and validation comparison runs both started with `cached=0`.
- Resource limits: none observed. Iteration ran as 229 chunks with 4 effective GPU workers; validation ran as 46 chunks with 4 effective GPU workers.
- Failed or restarted commands: one preliminary registration command used nonexistent helper names and exited 1, then the corrected registration command passed. The incumbent non-restart iteration run was superseded for cache validity. No evaluation command used for scoring failed.
- Nonfinite or unstable outputs: none reported. Candidate fast plus candidate/incumbent iteration and validation diagnostics used for scoring had `failed=False` and zero issues.

## Recommendation To Orchestrator

Report measured gate status only: fast passed, iteration promoted to validation, validation passed the measurement thresholds, and golden was not run. The Scorer does not accept or reject the candidate.

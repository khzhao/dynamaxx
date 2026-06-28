# Scoring Notes

## Gate Status

- Fast gate: passed using the pre-existing authorized fast artifact. Candidate fast primary_score=-0.8008235813719522, failed=False, issues=0, records=120.
- Registration gate: passed. Both the candidate and incumbent were listed by `dycore_model_names()` and constructible with `create_dycore_model()` as `DinosaurPrimitiveEquationsDycoreModel`.
- Iteration promotion gate: failed. Candidate primary_score=-0.8348723734291655; incumbent primary_score=-0.8348806410796545; iteration_delta=8.267650489002243e-06, below the +0.002 threshold. Candidate and incumbent diagnostics were clean.
- Iteration early day 1-5 mean RMSE guard: passed. Overall early mean RMSE relative change was 9.828690376106599e-05%, below the +2% threshold. By variable, 10m_u_component_of_wind changed by 0.00010527462374091582%, 2m_temperature changed by 9.569329566274759e-05%, geopotential_500 changed by 0.00014857044829655756%, and mean_sea_level_pressure changed by 6.11723607057409e-05%.
- Iteration variable+lead RMSE guard: passed. No variable+lead exceeded the +10% regression threshold; the largest positive variable+lead change was 10m_u_component_of_wind day 12 at 0.00507268124075087%.
- Validation acceptance gate: not run. Validation was skipped because iteration did not meet the +0.002 primary score promotion threshold.

## Measurement Lessons

- The theta-consistent Held-Suarez forcing candidate was effectively neutral on RMSE guardrails but did not clear the fixed primary-score promotion threshold.
- The primary-score movement was positive but tiny: +0.000008267650489002243 against a required +0.002, so this is not enough signal to justify validation.
- The largest variable+lead regression was 10m_u_component_of_wind day 12 at 0.00507268124075087%, far below the +10% guardrail.
- The largest variable+lead improvement was 10m_u_component_of_wind day 15 at -0.008011156034929362%.
- Future theta-forcing proposals should target a larger dynamical effect or a better-localized pressure/thermal coupling, because converting the weak-HS relaxation into theta space was nearly numerically identical under the fixed evaluation.

## Anomalies

- Cache reuse: candidate focused pytest, full pytest, and fast records were reused from the Implementer record as authorized. Compatible incumbent iteration artifacts were reused from `.logbook/leaderboard.json`.
- Validation skipped: this is expected protocol behavior after the failed iteration primary gate, not an infrastructure failure.
- Resource limits: none observed. Iteration used 229 chunks with 4 effective GPU workers; CPU count was 48, available RAM was about 174 GiB, and four L4 GPUs each reported 22566 MiB free before scoring.
- Failed or restarted commands: none during scoring.
- Nonfinite or unstable outputs: none reported. Candidate fast and iteration diagnostics had failed=False and issue_count=0.

## Recommendation To Orchestrator

Report the measured gate status only: fast passed, iteration did not promote to validation, validation was not run, and golden was not run. The Scorer does not accept or reject the candidate.

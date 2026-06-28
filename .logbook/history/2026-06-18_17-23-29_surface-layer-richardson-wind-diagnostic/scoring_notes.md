# Scoring Notes

## Gate Status

- Fast gate: passed using the pre-existing authorized fast artifact. Candidate fast primary_score=-0.8225154341252393, failed=False, issues=0, records=120.
- Iteration promotion gate: passed. Candidate primary_score=-0.8503285831632285; incumbent primary_score=-1.1021997794865541; iteration_delta=0.25187119632332566, above the +0.002 threshold. Diagnostics were clean for candidate and incumbent. Early day 1-5 mean RMSE relative change was -0.20660164995484745%, with no variable mean regression over 2%. No variable+lead RMSE regression exceeded 10%; worst positive variable+lead relative change was geopotential_500 day 13.0 at 0.0014906100606845295%.
- Validation acceptance gate: passed by measurement. Candidate primary_score=-0.8392576077353403; incumbent primary_score=-1.0904774361507537; validation_delta=0.25121982841541335, above the +0.001 threshold. Diagnostics were clean for candidate and incumbent. Early day 1-5 mean RMSE relative change was -0.21024965247733265%, with no variable mean regression over 2%. No variable+lead RMSE regression exceeded 10%; worst positive variable+lead relative change was 2m_temperature day 14.0 at 0.0024576258722063763%.

## Measurement Lessons

- The score gain is dominated by improved `10m_u_component_of_wind` RMSE. The best iteration improvement was 10m_u_component_of_wind day 15.0 at -43.98385998440271% relative RMSE change; the best validation improvement was 10m_u_component_of_wind day 14.0 at -44.22735238165948%.
- Other target variables were effectively unchanged: iteration worst positive RMSE regression was 0.0014906100606845295%, and validation worst positive RMSE regression was 0.0024576258722063763%, far below the 10% guardrail.
- The validation delta was close to the iteration delta, so the measured wind-diagnostic improvement appears stable across the fixed split.

## Anomalies

- Cache reuse: candidate pytest, `git diff --check`, and fast records were reused from the Implementer/Main Orchestrator records as authorized. Compatible incumbent iteration and validation artifacts were reused from the Orchestrator-provided leaderboard paths. Candidate iteration and validation both reported cached=0 at startup.
- Resource limits: none observed. Iteration used 229 chunks with 4 effective GPU workers; validation used 46 chunks with 4 effective GPU workers.
- Failed or restarted commands: none. Registration, candidate iteration, and candidate validation exited 0.
- Nonfinite or unstable outputs: none reported. Candidate fast, iteration, and validation diagnostics all had failed=False and issue_count=0.

## Recommendation To Orchestrator

Report the measured gate status only: fast passed, iteration promoted to validation, validation acceptance gates passed by measurement, and golden was not run. The Scorer does not accept or reject the candidate.

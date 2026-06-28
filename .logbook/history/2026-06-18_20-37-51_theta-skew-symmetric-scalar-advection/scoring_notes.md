# Scoring Notes

## Gate Status

- Fast gate: passed using the pre-existing authorized fast artifact. Candidate fast primary_score=-0.800745020086001, failed=False, issues=0, records=120.
- Registration gate: passed. Both the candidate and incumbent were listed by `dycore_model_names()` and constructible with `create_dycore_model()` as `DinosaurPrimitiveEquationsDycoreModel`.
- Iteration promotion gate: failed. Candidate primary_score=-0.8353205623225486; incumbent primary_score=-0.8348806410796545; iteration_delta=-0.000439921242894048, below the +0.002 threshold. Candidate and incumbent diagnostics were clean.
- Iteration early day 1-5 mean RMSE guard: passed. Overall early mean RMSE relative change was +0.022907203220216%, below the +2% threshold. By variable, 10m_u_component_of_wind changed by -0.069850130862370%, 2m_temperature changed by -0.036816261651554%, geopotential_500 changed by +0.030013893717601%, and mean_sea_level_pressure changed by +0.018524778787710%.
- Iteration variable+lead RMSE guard: passed. No variable+lead exceeded the +10% regression threshold; the largest positive variable+lead change was mean_sea_level_pressure day 15 at +0.131028012156075%.
- Validation acceptance gate: not run. Validation was skipped because iteration did not meet the +0.002 primary score promotion threshold.

## Measurement Lessons

- The skew-symmetric scalar advection candidate slightly worsened the fixed iteration primary score by -0.000439921242894048 relative to the theta-tendency incumbent.
- RMSE guardrails were clean and very small in magnitude: early day 1-5 aggregate RMSE changed by only +0.022907203220216%.
- The largest variable+lead regression was mean_sea_level_pressure day 15 at +0.131028012156075%, far below the +10% guardrail.
- The largest variable+lead improvement was 10m_u_component_of_wind day 4 at -0.082321765309455%, so the implementation appears nearly neutral at RMSE level but slightly harmful to the primary score aggregation.
- Future scalar-transport proposals should justify why the score aggregation should improve, not only why conservative/split-form transport is physically attractive, because this low-amplitude change did not clear the primary threshold.

## Anomalies

- Cache reuse: candidate focused pytest, full pytest, and fast records were reused from the Implementer record as authorized. Compatible incumbent iteration artifacts were reused from `.logbook/leaderboard.json`.
- Validation skipped: this is expected protocol behavior after the failed iteration primary gate, not an infrastructure failure.
- Resource limits: none observed. Iteration used 229 chunks with 4 effective GPU workers; CPU count was 48, available RAM was about 174 GiB, and four L4 GPUs each reported 22566 MiB free before/after scoring checks.
- Failed or restarted commands: none during scoring.
- Nonfinite or unstable outputs: none reported. Candidate fast and iteration diagnostics had failed=False and issue_count=0.

## Recommendation To Orchestrator

Report the measured gate status only: fast passed, iteration did not promote to validation, validation was not run, and golden was not run. The Scorer does not accept or reject the candidate.

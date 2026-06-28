# Scoring Notes

## Gate Status

- Fast gate: passed via reused Implementer artifact `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`; exact candidate `model_name`, `failed=False`, `issues=[]`, `records=120`, primary score `-1.1232864583588322`.
- Iteration promotion gate: passed. Candidate primary `-1.143975258592661` versus incumbent `-1.1486642287781768`, delta `+0.004688970185515728`; candidate diagnostics `failed=False`, issue count `0`. Worst early day 1-5 mean RMSE regression was `10m_u_component_of_wind` at `+0.135177550727686%`, below the 2% guardrail. Worst variable+lead RMSE regression was `10m_u_component_of_wind` at 24 h with `+0.5852716718076152%`, below the 10% guardrail.
- Validation acceptance gate measurement: passed as a measured gate, without making an accept/reject decision. Candidate primary `-1.1301883620649706` versus incumbent `-1.1354942896701432`, delta `+0.005305927605172567`; candidate diagnostics `failed=False`, issue count `0`. Worst early day 1-5 mean RMSE regression was `10m_u_component_of_wind` at `+0.1217093125612292%`, below the 2% guardrail. Worst variable+lead RMSE regression was `10m_u_component_of_wind` at 24 h with `+0.5788519865989503%`, below the 10% guardrail.

## Commands And Artifacts

- Registration confirmed with `uv run python` using `DYCORE_MODEL_FACTORIES` and `create_dycore_model`; candidate and incumbent both registered and construct with expected names.
- Full tests: `uv run pytest`, exit `0`; `123 passed, 2 skipped in 60.60 s`.
- Fast: reused `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init` from the Implementer record, then verified JSON and CSV paths.
- Iteration: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init --workers 4`, exit `0`, started `2026-06-17T06:55:24Z`, finished `2026-06-17T07:40:14Z`.
- Validation: `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init --workers 4`, exit `0`, started `2026-06-17T07:40:52Z`, finished `2026-06-17T07:51:08Z`.
- Candidate artifacts: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`, `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`, `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`, plus matching CSV files.
- Incumbent artifacts reused: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init.json`, `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init.json`, plus matching CSV files.

## Measurement Lessons

- The layer-mean hydrostatic initialization preserved the incumbent's main mass-field behavior and slightly improved primary score on both iteration and validation.
- Early `2m_temperature` and `geopotential_500` mean RMSE improved relative to the incumbent on both iteration and validation; the only positive early mean RMSE movement was a small `10m_u_component_of_wind` regression well below guardrail thresholds.
- Persistence rows are present in every JSON/CSV metrics file with duplicate `(channel_name, lead_hours)` keys. All scorer comparisons filtered exact evaluated `model_name` before computing RMSE deltas.

## Anomalies

- Cache reuse: candidate fast artifact reused after compatibility verification; incumbent iteration and validation artifacts reused from Orchestrator-supplied compatible leaderboard artifacts. Candidate iteration and validation were fresh runs with `cached=0`.
- Resource limits: none observed. Both fresh evals used GPU dispatch with requested/effective workers `4`.
- Failed or restarted commands: two initial registration probes used nonexistent registry helper names and exited `1`; the successful registry check used the actual registry API. No evaluation command failed or restarted.
- Nonfinite or unstable outputs: none observed; fast, iteration, and validation diagnostics all reported `failed=False` and zero issues.

## Recommendation To Orchestrator

Measured gates passed for fast, iteration promotion, and validation acceptance criteria. This is a measurement report only; accept/reject authority remains with the Orchestrator.

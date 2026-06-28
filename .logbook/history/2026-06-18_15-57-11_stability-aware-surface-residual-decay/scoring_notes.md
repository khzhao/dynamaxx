# Scoring Notes

## Gate Status

- Fast gate: passed using the pre-existing candidate fast record. `failed=False`, `issues=0`, `records=120`, `primary_score=-1.0749084840742946`.
- Registration gate: passed. Both the candidate and incumbent were listed by `dycore_model_names()` and constructible with `create_dycore_model()` as `DinosaurPrimitiveEquationsDycoreModel`.
- Iteration promotion gate: passed. Candidate primary score was `-1.1021997794865541`; incumbent primary score was `-1.1241936221835356`; delta was `+0.021993842696981458`, above the `+0.002` threshold. Candidate diagnostics were `failed=False`, `issues=0`.
- Iteration early lead 1-5 day mean RMSE guard: passed. Worst relative change was an improvement, `2m_temperature=-6.439308090963196%`; other variables were `10m_u_component_of_wind=-0.5763218836489706%`, `geopotential_500=-0.000013859844206197448%`, and `mean_sea_level_pressure=-0.0000038133757269382525%`.
- Iteration variable+lead RMSE guard: passed. No variable+lead exceeded the `+10%` regression threshold. The largest positive regression was `mean_sea_level_pressure` at day 14: `+0.001043216021196686%`.
- Validation acceptance gate: passed by measurement. Candidate primary score was `-1.0904774361507537`; incumbent primary score was `-1.1127999773519712`; delta was `+0.02232254120121757`, above the `+0.001` threshold. Candidate diagnostics were `failed=False`, `issues=0`.
- Validation early lead 1-5 day mean RMSE guard: passed. Worst relative changes were `geopotential_500=+0.000009751712723261476%` and `mean_sea_level_pressure=+0.000004029985897063112%`, both far below `+2%`; `2m_temperature=-6.42346079582575%` and `10m_u_component_of_wind=-0.5833540638885769%` improved.
- Validation variable+lead RMSE guard: passed. No variable+lead exceeded `+10%`. The largest positive regression was `geopotential_500` at day 9: `+0.0005729220533994537%`.

## Commands And Artifacts

- Reused pre-existing `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`: exit `0`, `80 passed in 65.99s`.
- Reused pre-existing `uv run pytest`: exit `0`, `146 passed, 2 skipped in 73.47s`.
- Reused pre-existing `git diff --check`: exit `0`.
- Reused pre-existing `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual`: exit `0`; raw outputs are `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual.json` and `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual.csv`.
- Ran `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual --workers 4`: exit `0`, started `2026-06-18T16:09:17Z`, finished `2026-06-18T17:00:35Z`; raw outputs are `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual.csv`.
- Ran `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual --workers 4`: exit `0`, started `2026-06-18T17:01:00Z`, finished `2026-06-18T17:12:27Z`; raw outputs are `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual.json` and `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual.csv`.
- Reused compatible incumbent iteration artifacts: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.csv`.
- Reused compatible incumbent validation artifacts: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.json` and `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.csv`.

## Measurement Lessons

- Lesson: the candidate produced consistent primary-score gains on both iteration and validation, with deltas `+0.021993842696981458` and `+0.02232254120121757`.
- Lesson: most of the measurable RMSE movement is in early `2m_temperature`, which improved by about `6.4%` over days 1-5 in both iteration and validation.
- Lesson: pressure and 500 hPa geopotential changes are numerically tiny; the largest positive RMSE regressions were below `0.002%`, far inside guardrails.

## Anomalies

- Cache reuse: candidate fast and test records were reused from pre-existing Implementer/Main Orchestrator records. Incumbent iteration and validation metrics were reused from compatible leaderboard artifacts. Fresh candidate iteration and validation runs both reported `cached=0`.
- Resource limits: worker count was `4`; evaluator used GPU dispatch with `gpu_count=4` and worker devices `0:0,1:1,2:2,3:3`. Free disk after scoring was about `4.1T`.
- Failed or restarted commands: a non-gate exploratory registration probe attempted to import `list_models` from `dynamaxx.dycore.registry` and exited `1` because this repository exposes `dycore_model_names()` instead. The corrected registration confirmation exited `0`.
- Nonfinite or unstable outputs: none reported by evaluator diagnostics.

## Recommendation To Orchestrator

Report the measured gate status and decide separately. By measurement, fast, iteration promotion, and validation acceptance gates all passed, with clean diagnostics and no RMSE guardrail violations.

# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_symmetric_diffusion` exited 0 with `failed=False`, `issues=0`, `records=120`, and primary score `-1.0964177761687355`.
- Iteration promotion gate: failed on primary score. Candidate iteration primary score was `-1.1242117369530207`; incumbent iteration primary score was `-1.1241936221835356`; candidate-minus-incumbent delta was `-0.000018114769485100268`, below the required `+0.002` threshold.
- Iteration diagnostics gate: passed. Candidate iteration diagnostics reported `failed=False` and `issues=0`; reused incumbent iteration diagnostics also reported `failed=False` and `issues=0`.
- Early day 1-5 mean RMSE guard: passed. Largest relative regression was `10m_u_component_of_wind` at `0.0002377748010882197` (`0.02377748010882197%`), below the `2%` guardrail.
- Any variable+lead RMSE guard: passed. Largest relative regression was `10m_u_component_of_wind` at 48 hours, `0.0002827308327868483` (`0.02827308327868483%`), below the `10%` guardrail.
- Validation acceptance gate: not evaluated. Per protocol and Orchestrator instruction, validation was not run because the iteration primary score delta did not reach `+0.002`.

## Commands And Artifacts

- Registration confirmation: `uv run python - <<'PY' ... PY` exited 0 and confirmed both candidate and incumbent instantiate as `DinosaurPrimitiveEquationsDycoreModel`.
- Tests: `uv run pytest` was not rerun by Scorer; recorded Orchestrator-provided passing test result `146 passed, 2 skipped in 71.02s`.
- Fast command: `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_symmetric_diffusion`, exit 0.
- Iteration command: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_symmetric_diffusion --workers 4`, exit 0.
- Validation command: `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_symmetric_diffusion --workers 4`, not run because iteration did not promote.
- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_symmetric_diffusion.json`.
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_symmetric_diffusion.csv`.
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_symmetric_diffusion.json`.
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_symmetric_diffusion.csv`.
- Reused incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.json`.
- Reused incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.csv`.
- Compatible incumbent validation artifacts exist at `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.json` and `.csv`, but were not used for candidate validation comparison because candidate validation was skipped.

## Guardrail Calculations

- Day 1-5 mean RMSE, `10m_u_component_of_wind`: candidate `8.67176529652168`, incumbent `8.669703859411015`, relative change `0.0002377748010882197`.
- Day 1-5 mean RMSE, `2m_temperature`: candidate `7.357167638028957`, incumbent `7.356441931023136`, relative change `0.0000986491856560523`.
- Day 1-5 mean RMSE, `mean_sea_level_pressure`: candidate `1000.2826049056381`, incumbent `1000.2811415587845`, relative change `0.0000014629355615802808`.
- Day 1-5 mean RMSE, `geopotential_500`: candidate `735.8901411488262`, incumbent `735.903165954637`, relative change `-0.000017699075657517938`.
- Max variable+lead RMSE regression by variable: `10m_u_component_of_wind` 48h `0.0002827308327868483`; `2m_temperature` 24h `0.00011726112374454978`; `geopotential_500` 24h `0.000038495549120609596`; `mean_sea_level_pressure` 24h `0.00003491882808459579`.
- CSV guardrail calculations filtered rows by exact `model_name`. The raw CSVs also include persistence baseline rows, so unfiltered row-key comparisons would be incorrect.

## Measurement Lessons

- The symmetric diffusion split produced numerically tiny RMSE changes relative to the incumbent and a slight primary-score regression. Future proposals around this mechanism need a larger behavioral change or a more targeted stability/accuracy rationale to clear the `+0.002` iteration threshold.
- Because evaluator CSVs include persistence rows in addition to model rows, scorer utilities should always filter by exact `model_name` before computing candidate-versus-incumbent guardrails.

## Anomalies

- Cache reuse: incumbent iteration and validation artifacts were reused from the leaderboard-compatible paths provided by the Orchestrator. Candidate iteration reported `cached=0`.
- Resource limits: no resource failures observed. Iteration output reported `requested_workers=4`, `effective_workers=4`, `gpu_count=4`, and device dispatch `0:0,1:1,2:2,3:3`.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by evaluator diagnostics.

## Recommendation To Orchestrator

Report measured gate status only: the candidate passed fast, diagnostics, and RMSE guardrails, but failed iteration promotion due to primary delta `-0.000018114769485100268`; validation was therefore not run.

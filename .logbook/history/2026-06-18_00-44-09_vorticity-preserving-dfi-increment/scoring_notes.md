# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi` exited 0 with `failed=False`, 0 diagnostic issues, 120 records, and primary score `-1.1257291802745486`.
- Iteration promotion gate: did not promote. Candidate iteration primary was `-1.1463108571625462`; reused incumbent iteration primary was `-1.143975258592661`; delta was `-0.002335598569885189`, below the required `+0.002`.
- Iteration diagnostics: clean. Candidate iteration `failed=False`, 0 issues; incumbent iteration `failed=False`, 0 issues.
- Iteration early day 1-5 mean RMSE guardrail: clean. No variable exceeded the `>2%` regression threshold. Worst early mean RMSE relative delta was `0.0029875295933590174` for `mean_sea_level_pressure`.
- Iteration variable+lead RMSE guardrail: clean. No variable+lead exceeded the `>10%` regression threshold. Worst relative delta was `0.006528434057403665` for `10m_u_component_of_wind` at lead hour 24.
- Validation acceptance gate: not run because the iteration promotion gate did not pass. This follows the Orchestrator instruction that validation may run only if iteration promotes.

## Commands And Exit Statuses

- `uv run python -c "from dynamaxx.dycore.registry import dycore_model_names; required=('dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi','dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init'); names=set(dycore_model_names()); missing=[name for name in required if name not in names]; print('registered=' + ','.join(name for name in required if name in names)); print('missing=' + ','.join(missing)); raise SystemExit(1 if missing else 0)"` -> exit 0.
- `uv run pytest` -> exit 0; `130 passed, 2 skipped in 67.79s`.
- `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi` -> exit 0.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi --workers 4` -> exit 0.
- `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi --workers 4` -> not run; skipped because iteration did not promote.
- `golden` was not run.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_vort_preserving_dfi.csv`
- Candidate validation JSON/CSV: not produced because validation was skipped.
- Reused incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Reused incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`
- Compatible incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Compatible incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`

## Cache Reuse

- Candidate fast: fresh run.
- Candidate iteration: fresh run. The evaluator reported `cached=0 pending=229`.
- Incumbent iteration: reused the compatible incumbent artifacts supplied by the Orchestrator.
- Incumbent validation: compatible artifacts were available, but not used for a validation gate because candidate validation was not run.

## Anomalies

- An exploratory `jq` probe for a non-existent `.metrics` key exited with status 5. It was read-only and did not affect scoring.
- Raw metric JSON artifacts include both evaluated-model rows and persistence baseline rows. Guardrail calculations must filter by `model_name`; an unfiltered `channel_name`/`lead_hours` join can accidentally compare the candidate against persistence.
- No resource failures, command restarts, nonfinite diagnostics, or unstable-output issues were observed in the required evaluation commands.

## Measurement Lessons

- Always filter `records` by the evaluated `model_name` before computing candidate-versus-incumbent RMSE guardrails.
- The candidate preserved clean diagnostics and stayed inside the RMSE guardrails, but did not improve the iteration primary score. The scoring result is measurement-only; the Orchestrator decides the final disposition.

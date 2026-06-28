# Scoring Notes

## Gate Status

- Fast gate: passed by verifying the existing candidate fast artifact. Primary score was `-1.120810250964844`, `failed=False`, and issue count was `0`.
- Iteration promotion gate: did not pass. Candidate primary was `-1.144930302953247`; incumbent primary was `-1.143975258592661`; delta was `-0.000955044360586`, below the required `+0.002`.
- Validation acceptance gate: not run. Protocol allows validation only after the iteration gate passes.

## Iteration Guardrails

- Diagnostics: candidate `failed=False`, candidate issues `0`; incumbent `failed=False`, incumbent issues `0`.
- Early day 1-5 mean RMSE regressions: no variable exceeded the `2%` threshold. Positive regressions were `geopotential_500` at `+0.3660%` and `mean_sea_level_pressure` at `+0.1530%`; `10m_u_component_of_wind` and `2m_temperature` improved slightly.
- Variable plus lead RMSE regressions: no pair exceeded the `10%` threshold. The largest positive regression was `mean_sea_level_pressure` at lead `168` hours, `+1.0107%`.

## Commands

- `uv run python -c "from dynamaxx.dycore.registry import dycore_model_names; names=set(dycore_model_names()); requested={'dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_extrap','dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init'}; missing=sorted(requested-names); print('registered=' + ','.join(sorted(requested))); print('missing=' + ','.join(missing)); raise SystemExit(1 if missing else 0)"`: exit `0`.
- `uv run pytest`: exit `0`; `128 passed, 2 skipped in 63.69s`.
- `uv run python - <<'PY' ... verify existing fast artifact ... PY`: exit `0`; reused `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_extrap.json`.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_extrap --workers 4`: exit `0`.
- `uv run python - <<'PY' ... exact model-name iteration comparison ... PY`: exit `0`.

## Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_extrap.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_extrap.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_extrap.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_bounded_extrap.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`
- Incumbent validation JSON available but not used because validation was skipped: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Incumbent validation CSV available but not used because validation was skipped: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`

## Measurement Lessons

- Lesson: bounded log-pressure initialization extrapolation kept diagnostics clean and stayed within RMSE guardrails, but did not improve the aggregate iteration primary score relative to the incumbent.
- Lesson: exact model-name filtering was necessary because metric artifacts include persistence rows alongside candidate or incumbent rows.

## Anomalies

- Cache reuse: reused the Orchestrator-provided incumbent iteration artifacts and the existing candidate fast artifact. Candidate iteration reported `cached=0`.
- Resource limits: none observed.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by diagnostics.

## Recommendation To Orchestrator

Report the measured gate status and caveats only. The candidate did not promote to validation under the fixed iteration gate, but the Scorer does not accept or reject candidates.

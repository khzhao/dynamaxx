# Scoring Notes

## Gate Status

- Unit tests: passed using Implementer-provided `uv run pytest` record (`178 passed, 2 skipped`) and focused dycore test record (`112 passed`).
- Fast gate: passed using readable Implementer-provided fast JSON; `failed=False`, `issues=0`, `records=120`, `primary_score=-0.7989254063123296`.
- Iteration gate: did not promote to validation. Candidate iteration primary score was `-0.8308818797588234`; incumbent iteration primary score was `-0.8308832822743712`; delta was `+0.0000014025155478103457`, below the required `+0.002`.
- Iteration diagnostics: passed for candidate and incumbent (`failed=False`, `issues=0`).
- Iteration RMSE guardrails: passed. No day 1-5 mean RMSE regression exceeded `2%`; no variable+lead RMSE regression exceeded `10%`. The largest variable+lead RMSE regression was `+0.00748325882069714%` for `geopotential_500` at day 12.
- Validation gate: not run because the iteration promotion gate failed.
- Golden: not run.

## Cache Reuse

- Iteration incumbent metrics were reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter.json` and matching CSV.
- Reuse checks passed: requested incumbent matched the leaderboard incumbent, the leaderboard fingerprint covered `iteration`, target variables and lead days matched, the eval/registry last-touch commit matched `c359ee1b016ccd92412585997a799a7c644a65c5`, the incumbent artifact was readable and finite, and the candidate was registered side-by-side.
- The registry has uncommitted candidate additions. A scorer-side factory check verified the incumbent registry key still creates the theta-recenter incumbent with `apply_log_surface_pressure_spectral_smoothing=False`; the candidate differs only by name and the smoother flag.
- Validation cache reuse was not applicable because validation was not run.

## Commands

- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`: exit 0, Implementer-provided, `112 passed`.
- `uv run pytest`: exit 0, Implementer-provided, `178 passed, 2 skipped`.
- `git diff --check`: exit 0, Implementer-provided.
- `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logp_spectral_smoother`: exit 0, Implementer-provided and JSON verified readable.
- `uv run python - <<'PY' ... import list_dycore_models ... PY`: exit 1; failed because that helper does not exist.
- `uv run python - <<'PY' ... verify DYCORE_MODEL_FACTORIES registration and side-by-side fields ... PY`: exit 0.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logp_spectral_smoother --workers 4`: exit 0.
- `uv run python - <<'PY' ... compute guardrails using model rows only ... PY`: exit 0.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logp_spectral_smoother.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logp_spectral_smoother.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logp_spectral_smoother.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_logp_spectral_smoother.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter.csv`

## Measurement Lessons

- The candidate is numerically clean but nearly indistinguishable from the incumbent on iteration primary score; the improvement is about `0.07%` of the required promotion delta.
- Evaluation JSON includes both model rows and persistence reference rows. Candidate-versus-incumbent guardrails must filter `record.model_name` to the evaluated dycore names before comparing RMSE.
- This smoother did not introduce guardrail-scale RMSE harm, but its measured benefit is too small to justify validation under the fixed protocol.

## Anomalies

- A registration check was retried after using a nonexistent helper; the corrected check passed.
- No resource failures, restarted evaluation commands, nonfinite outputs, or unstable diagnostics were observed.

## Recommendation To Orchestrator

Report the measured gate status only. This Scorer role does not accept or reject the candidate.

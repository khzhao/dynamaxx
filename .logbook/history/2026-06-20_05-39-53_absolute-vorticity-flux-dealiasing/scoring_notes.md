# Scoring Notes

## Gate Status

- Pytest gate: recorded from Orchestrator as passed, `193 passed, 2 skipped in 119.32s`; not rerun because source files were not edited afterward except logbook history files.
- Fast gate: passed. Command exited `0`; candidate diagnostics `failed=False`, issues `0`, primary score `-0.5476771846790718`.
- Iteration gate: did not promote to validation. Candidate score `-0.5318825727690968` versus incumbent `-0.5320532698936880`, delta `+0.00017069712459117`; required delta is `+0.002`.
- Iteration diagnostics: candidate `failed=False`, issues `0`.
- RMSE guardrails: passed. Largest early day-1..5 mean RMSE regression was `0.013498%` for `10m_u_component_of_wind`; largest variable+lead RMSE regression was `0.026760%` for `2m_temperature` at `12` days.
- Validation gate: not run because iteration promotion failed. `golden` was not run.

## Commands

- `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_av_flux_dealias` exited `0`.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_av_flux_dealias --workers 4` exited `0`.
- `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_av_flux_dealias --workers 4` was not run because the iteration primary-score gate failed.

## Incumbent Cache Reuse

- Iteration incumbent cache was reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.csv`.
- Validation incumbent cache was checked and recorded from `.logbook/leaderboard.json`: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.json` and `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual.csv`. It was not used for a candidate validation comparison because validation was not run.
- Cache checks passed: requested incumbent matched the leaderboard incumbent; fingerprint data path, target variables, lead range, protocols, and eval code commit matched; JSON/CSV artifacts existed; primary scores were finite; model rows needed for guardrails were present.
- Incumbent was not rerun. Candidate source edits do not invalidate the accepted incumbent cache under `roles/SCORER.md`.

## RMSE Guardrail Summary

| Guardrail | Worst case | Relative delta | Threshold | Status |
| --- | --- | ---: | ---: | --- |
| Early day-1..5 mean RMSE | `10m_u_component_of_wind` | `0.013498%` | `2.000000%` | passed |
| Variable+lead RMSE | `2m_temperature` at `12` days | `0.026760%` | `10.000000%` | passed |

## Measurement Lessons

- The absolute-vorticity flux dealiasing path is numerically stable under fast and iteration protocols, but its iteration improvement is effectively neutral and far below the promotion threshold.
- The metric movement is consistent with a very small, product-local perturbation: clean diagnostics and clean RMSE guardrails, but no meaningful primary-score lift.

## Anomalies

- No failed commands, worker restarts, nonfinite diagnostics, or cache invalidation were observed.
- Iteration completed 229 chunks with `--workers 4` and wrote the expected top-level JSON/CSV artifacts.

## Recommendation To Orchestrator

Do not run validation for this candidate state. Return to the Orchestrator for the protocol decision or for the next/revised idea; Scorer does not accept or reject the candidate.

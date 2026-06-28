# Scoring Notes

## Gate Status

- Fast gate: passed. Command exited 0 with `failed=false`, `issues=0`, `records=120`, and primary score `-0.5306873103410816`.
- Iteration promotion gate: did not pass. Candidate iteration primary was `-0.5150755275557011`; cached incumbent iteration primary was `-0.5150627015910243`; delta was `-0.00001282596467677699`, below the required `+0.002`.
- Iteration diagnostics were clean (`failed=false`, `issues=0`), the day 1..5 mean RMSE guardrail passed for all target variables, and the worst variable-lead RMSE regression was `2.2378814357182364e-7%` at `10m_u_component_of_wind` lead hour 96, well below the `10%` guardrail.
- Validation acceptance gate: not evaluated. Validation was allowed only after iteration promotion, so the candidate validation command was skipped.

## Cache Reuse

- Incumbent iteration metrics were reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json` and matching CSV.
- Incumbent validation metrics were checked and valid but not used for a candidate validation comparison because the iteration gate failed.
- Cache validity checks passed: requested incumbent matched the leaderboard incumbent, `HEAD` matched `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`, the fingerprint matched data path, target variables, lead days, and protocols, artifacts were readable, primary scores were finite, and required guardrail records were present.
- No incumbent evaluation was run.

## Measurement Lessons

- The DFI-balanced analysis-offset Held-Suarez equilibrium variant produced numerically clean fast and iteration forecasts.
- Iteration RMSE changes versus the incumbent were effectively at roundoff scale, but the primary score moved slightly negative, so the candidate did not earn validation.
- Future variants in this area should target a larger dynamical or diagnostic difference before spending validation budget.

## Anomalies

- Resource limits: none observed. Iteration ran with `--workers 4` and completed 229 chunks.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported in fast or iteration diagnostics.
- Golden: not run, as prohibited.

## Recommendation To Orchestrator

Report the measured gate status and caveats above. This Scorer artifact does not accept or reject the candidate.

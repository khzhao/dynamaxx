# Scoring Notes

## Gate Status

- Unit tests: passed using Implementer-provided full `uv run pytest` record (`176 passed, 2 skipped`); not rerun by Scorer.
- Fast gate: passed from readable provided artifact. Candidate fast diagnostics were `failed=False`, `issues=0`, with `primary_score=-1.152487804407429`.
- Iteration promotion gate: failed. Candidate iteration command exited 0, but metrics reported `failed=True`, `issues=6`, and `primary_score=-Infinity`.
- Validation acceptance gate: not run because the iteration promotion gate failed.
- Golden: not run.

## Iteration Measurements

- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_zonal_recenter.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_zonal_recenter.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter.csv`
- Candidate primary score: `-Infinity`
- Incumbent primary score: `-0.8308832822743712`
- Primary delta: `-Infinity`

## Guardrails

- Diagnostics: failed. Iteration produced five `nonfinite_forecast` error issues and one `nonfinite_metric` error issue.
- Early day 1-5 mean RMSE regression threshold (`<= 2%`): failed. Regressions were `+8.6718%` for `10m_u_component_of_wind`, `+7.8460%` for `geopotential_500`, and `+2.2718%` for `mean_sea_level_pressure`; `2m_temperature` improved by `-2.8764%`.
- Variable+lead RMSE regression threshold (`<= 10%`): failed. Finite threshold violations were `10m_u_component_of_wind` day 4 (`+10.6240%`), `geopotential_500` day 5 (`+14.0274%`), and `10m_u_component_of_wind` day 5 (`+14.6491%`).
- Nonfinite model metric rows: 40 candidate model rows were nonfinite for all four target variables from lead days 6-15.

## Cache Reuse

- Iteration incumbent: reused from `.logbook/leaderboard.json`. The requested incumbent matched the leaderboard incumbent, the recorded iteration artifact was readable with finite primary score and clean diagnostics, `src/dynamaxx/eval` had no committed or uncommitted changes relative to the accepted incumbent eval-code commit, and the candidate registration was side-by-side with incumbent factory flags still `apply_theta_layer_mean_recentering=True` and `apply_theta_zonal_mean_recentering=False`.
- Validation incumbent: not reused or recomputed because candidate validation was not run after iteration failed.
- The current HEAD `8ead91209dfbd2abc3ffc31082653cf29aa962dd` differs from accepted incumbent commit `c359ee1b016ccd92412585997a799a7c644a65c5` only in `roles/SCORER.md`; uncommitted registry changes add the candidate key without changing the incumbent key.

## Measurement Lessons

- Fast is not sufficient for this recentering family; the candidate passed fast but became nonfinite at iteration lead day 6 and later.
- Guardrail calculations must filter evaluation records by the scored `model_name`; the metrics files also contain persistence reference rows.
- The zonal theta recentering idea showed early 2m temperature improvement but caused broad dynamical instability and early RMSE regressions in wind, geopotential, and pressure.

## Anomalies

- Failed or restarted commands: one initial registration probe failed because it used nonexistent registry helper names. It was rerun with the actual `dycore_model_names` and `create_dycore_model` API and confirmed both models are registered.
- Resource limits: none observed; the candidate iteration completed with 4 workers.
- Nonfinite or unstable outputs: present in candidate iteration diagnostics and metric rows.

## Recommendation To Orchestrator

Report the measured gate status and caveats only. Scorer does not accept or reject candidates.

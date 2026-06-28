# Scoring Notes

## Gate Status

- Fast gate: passed by the Implementer with `failed=False`, `issues=0`, and
  `primary_score=-0.519179`.
- Iteration gate: passed. Candidate iteration primary score was
  `-0.532053269893688`; cached incumbent iteration primary score was
  `-0.5719873627530224`; delta was `+0.03993409285933447`, above the `+0.002`
  promotion threshold.
- Iteration diagnostics: passed with `failed=False` and `issues=0`.
- Iteration guardrails: passed. No day 1-5 variable mean RMSE regression
  exceeded `2%`; no variable+lead RMSE regression exceeded `10%`.
- Validation gate: passed. Candidate validation primary score was
  `-0.5219023378614627`; cached incumbent validation primary score was
  `-0.562579968224105`; delta was `+0.04067763036264238`, above the `+0.001`
  acceptance threshold.
- Validation diagnostics: passed with `failed=False` and `issues=0`.
- Validation guardrails: passed. No day 1-5 variable mean RMSE regression
  exceeded `2%`; no variable+lead RMSE regression exceeded `10%`.
- Golden: not run.

## Cache Reuse

Incumbent iteration and validation metrics were reused from
`.logbook/leaderboard.json` and its recorded artifacts. They were not
recomputed.

The cache was valid because the requested incumbent matched the leaderboard
incumbent, the incumbent artifacts were present and finite, the artifact
primary scores matched the leaderboard values, and committed changes since the
accepted dycore commit only touched role policy files. Candidate source edits
do not invalidate the accepted incumbent cache under the current policy.

## Commands And Artifacts

- Candidate fast: `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual`
- Candidate iteration: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual --workers 4`
- Candidate validation: `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual --workers 4`
- Candidate metrics are under `outputs/eval/*_scale_surface_residual.json` and
  matching `.csv` files.
- Cached incumbent metrics are the leaderboard `iteration_*_si_offcenter` and
  `validation_*_si_offcenter` JSON/CSV files.

## Measurement Lessons

- Scale-separated residual memory produced a large, clean primary-score gain
  on both iteration and validation.
- The improvement is dominated by 2 m temperature RMSE reductions. The largest
  early 10 m wind mean RMSE regression stayed below `0.55%`, well inside the
  `2%` guardrail.
- This candidate validates the idea that broad near-surface residual memory can
  be useful when separated from high-wavenumber residual noise.

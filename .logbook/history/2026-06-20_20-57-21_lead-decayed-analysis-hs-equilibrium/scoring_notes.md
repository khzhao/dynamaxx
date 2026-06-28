# Scoring Notes

## Gate Status

- Registration: confirmed after correcting the registry helper used by the probe. Candidate and incumbent are both present in `dycore_model_names()`.
- Full test gate: passed. `uv run pytest` exited `0` with `201 passed, 2 skipped in 135.99s`.
- Fast gate: passed. Candidate fast exited `0` with `failed=false`, `issues=0`, `records=120`, primary score `-0.5306019403633883`.
- Iteration promotion gate: did not pass. Candidate primary score `-0.514816113028215`; cached incumbent primary score `-0.5150627015910243`; delta `+0.0002465885628093467`, below the `+0.002` promotion threshold. Candidate diagnostics were clean and RMSE guardrails were clean.
- Validation acceptance gate: not measured. Candidate validation was skipped because the iteration promotion gate did not pass.
- Golden: not run. Golden is prohibited for this scoring task.

## Commands

- `python - <<'PY' ... from dynamaxx.dycore.registry import get_model ... PY`: exit status `1`. This probe used a nonexistent helper and failed with `ImportError`.
- `python - <<'PY' ... from dynamaxx.dycore.registry import dycore_model_names ... PY`: exit status `0`; candidate registered `true`, incumbent registered `true`.
- `uv run pytest`: exit status `0`; `201 passed, 2 skipped in 135.99s`.
- `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_decay`: exit status `0`.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_decay --workers 4`: exit status `0`.
- `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_decay --workers 4`: skipped; iteration promotion gate did not pass.

No incumbent evaluation commands were run.

## Diagnostics

- Candidate fast: `failed=false`, issue count `0`.
- Candidate iteration: `failed=false`, issue count `0`.
- Candidate validation: not run.
- Cached incumbent iteration: `failed=false`, issue count `0`.
- Cached incumbent validation: `failed=false`, issue count `0`.

## RMSE Guardrails

Iteration early day-1-through-day-5 mean RMSE regressions:

- `10m_u_component_of_wind`: `-0.03445852711659334%`.
- `2m_temperature`: `-0.0825447394376603%`.
- `geopotential_500`: `+0.029548798666215903%`.
- `mean_sea_level_pressure`: `-0.058498855366962386%`.

Iteration max variable-lead RMSE regressions by variable:

- `10m_u_component_of_wind`, day `15.0` (`360` hours): `+2.9583314085064374%`; candidate RMSE `7.125923443906837`, incumbent RMSE `6.9211722319327444`.
- `2m_temperature`, day `1.0` (`24` hours): `-0.048423575053316924%`; candidate RMSE `3.0820168243389987`, incumbent RMSE `3.0835099701036484`.
- `geopotential_500`, day `15.0` (`360` hours): `+0.5234464756087811%`; candidate RMSE `1326.0686850932289`, incumbent RMSE `1319.1635698791813`.
- `mean_sea_level_pressure`, day `15.0` (`360` hours): `+0.06466348452077325%`; candidate RMSE `1666.1083256806921`, incumbent RMSE `1665.031658192131`.

Guardrail summary: no day-1-through-day-5 mean RMSE regression exceeded the `2%` limit, and no variable-lead RMSE regression exceeded the `10%` limit. The overall largest relative RMSE regression was `10m_u_component_of_wind` at day `15.0`, `+2.9583314085064374%`.

Guardrail calculation note: each iteration JSON contains 120 records: 60 evaluated-model rows and 60 persistence rows. RMSE guardrails used only rows whose `model_name` matched the candidate or incumbent.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_decay.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_decay.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_decay.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_decay.csv`
- Candidate validation JSON: not produced.
- Candidate validation CSV: not produced.
- Cached incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Cached incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`
- Cached incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.json`
- Cached incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq.csv`

## Cache Reuse

- Incumbent iteration metrics were reused from `.logbook/leaderboard.json`; no incumbent iteration command was run.
- Validation cache status is recorded explicitly: cached incumbent validation artifact was checked and remains valid, but it was not used for a candidate comparison because candidate validation was skipped.
- Reuse checks passed for iteration and validation: requested incumbent equals leaderboard incumbent; current `HEAD` equals incumbent commit and leaderboard eval code commit `6094c73fe9b98b46c3ac9bfbb430bafd332d628f`; leaderboard fingerprint matches data path, target variables, lead range, and protocols; artifacts exist, are readable, contain incumbent model rows, have finite primary scores, have 120 records, and have clean diagnostics.
- No recomputation reason: the cache is valid under `roles/SCORER.md`; candidate source edits in adapter, registry, and tests do not invalidate accepted incumbent artifacts; no fixed protocol, metric, data, split, target-variable, or lead-range change was part of this candidate.

## Measurement Lessons

- The lead-decayed analysis-HS offset produced a near-neutral iteration result against the accepted constant-offset incumbent: a clean `+0.0002465885628093467` primary delta, but not enough to clear the fixed promotion gate.
- RMSE guardrails remained clean. The largest relative regression was long-lead `10m_u_component_of_wind`, even though the candidate changed only the thermal equilibrium offset, suggesting the taper has weak coupled mass-wind effects at long lead.
- Future scoring scripts should keep filtering metric records by `model_name`; the JSON includes persistence rows sharing the same channel and lead keys.

## Anomalies

- Cache reuse: no anomaly. Incumbent cache was reused according to Orchestrator instruction and role policy.
- Resource limits: no resource failure observed. Iteration dispatched with requested workers `4`, effective workers `4`, GPU count `4`.
- Failed or restarted commands: the first registry probe failed because it imported the wrong helper name; the corrected registry check passed. No evaluation command failed or restarted.
- Nonfinite or unstable outputs: none reported by diagnostics.

## Recommendation To Orchestrator

Measured iteration promotion gate does not pass under the fixed protocol and cached-incumbent comparison. Scorer does not accept or reject the candidate.

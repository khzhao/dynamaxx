# Scoring Notes

## Scope

- Role: Scorer
- Candidate: `dino_obulk_sstice`
- Incumbent: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf`
- History directory: `.logbook/history/2026-06-22_07-54-50_sst-sea-ice-ocean-flux-anchor`
- Worker count: 4
- Golden run: not run

## Cache Reuse

Incumbent iteration metrics were reused from the leaderboard artifacts. The reused files were `outputs/eval/iteration_ocean_bulk_sensible_heat_flux.json` and `outputs/eval/iteration_ocean_bulk_sensible_heat_flux.csv`. Cache checks passed: the requested incumbent matched `.logbook/leaderboard.json`, the fingerprint data path, protocols, target variables, lead range, and eval-code commit matched, the JSON/CSV files existed, the JSON was readable, the primary score was finite, and the artifact contained the incumbent model rows needed for guardrail comparisons.

Incumbent validation metrics were also checked from the leaderboard artifacts (`outputs/eval/validation_ocean_bulk_sensible_heat_flux.json` and `outputs/eval/validation_ocean_bulk_sensible_heat_flux.csv`), but validation comparison was not reached because the iteration promotion gate failed. No incumbent rerun was performed. Candidate source edits were not treated as cache invalidation, per `roles/SCORER.md`.

## Unit Test Gate

The unit-test gate was verified from `.logbook/history/2026-06-22_07-54-50_sst-sea-ice-ocean-flux-anchor/implementation.md` rather than rerun. That record contains the Orchestrator full gate: `uv run pytest` passed with 216 passed and 2 skipped in 142.99s for this exact candidate diff. The current task stated that the working tree diff matched `candidate.diff` after stash apply.

## Candidate Runs

- Fast command: `uv run dynamaxx-eval fast --model dino_obulk_sstice`
- Fast exit status: 0
- Fast primary score: -0.4416690046386025
- Fast diagnostics: failed=False, issues=0
- Iteration command: `uv run dynamaxx-eval iteration --model dino_obulk_sstice --workers 4`
- Iteration exit status: 0
- Iteration resume: 223 cached chunks, 6 pending chunks, 229/229 chunks complete after run
- Iteration diagnostics: failed=False, issues=0

## Iteration Gate

- Candidate primary score: -0.4270088457239165
- Cached incumbent primary score: -0.4270118753609274
- Primary delta: 0.0000030296370109
- Required iteration delta: +0.002
- Primary gate: fail
- Early day 1-5 mean RMSE regression: 1.5843645488412374e-07 (0.000015843645%), threshold <= 2%, gate=pass
- Worst variable+lead RMSE regression: 7.3969001362003241e-06 (0.000739690014%) at `10m_u_component_of_wind` lead 192h, threshold <= 10%, gate=pass
- Diagnostics gate: pass
- Overall iteration promotion gate: fail

Validation was not run because the iteration promotion gate failed. This follows the task constraint that validation is allowed only if iteration promotion passes.

## Measurement Notes

The iteration metric JSON contains both evaluated-model rows and persistence reference rows for each variable/lead pair. Guardrails in `scores.json` filter to `model_name == 'dino_obulk_sstice'` for the candidate and `model_name == 'dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf'` for the incumbent before comparing RMSE.

No scoring anomalies occurred. The known long-filename top-level writing anomaly did not occur for the short candidate name; standard JSON and CSV files were written at `outputs/eval/iteration_dino_obulk_sstice.json` and `outputs/eval/iteration_dino_obulk_sstice.csv`.

## Recommended Orchestrator Action

The Scorer does not accept or reject candidates. The measured iteration primary delta is below the promotion threshold, so the Orchestrator should record that validation was not reached and make the terminal decision for this iteration from the failed iteration promotion gate.

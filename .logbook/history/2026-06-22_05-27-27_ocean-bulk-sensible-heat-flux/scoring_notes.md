# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model ..._ocean_bulk_shf` exited 0, wrote official JSON/CSV artifacts, and reported diagnostics failed false with 0 issues.
- Iteration promotion gate: passed by recovered fixed-metric records. Candidate primary `-0.42701187536092744` versus cached incumbent `-0.49843977504709575`, delta `+0.0714278996861683`; diagnostics failed false with 0 issues; all early day 1-5 mean RMSE regressions were <= 2%; worst variable+lead RMSE regression was `+0.003001933955484315` for `10m_u_component_of_wind` at 72 hours, within the 10% guardrail.
- Validation acceptance-support gate: passed by recovered fixed-metric records. Candidate primary `-0.417391902036791` versus cached incumbent `-0.48771725322193726`, delta `+0.07032535118514627`; diagnostics failed false with 0 issues; all early day 1-5 mean RMSE regressions were <= 2%; worst variable+lead RMSE regression was `+0.002187786775164069` for `10m_u_component_of_wind` at 72 hours, within the 10% guardrail.

## Commands Run

- Verified, not rerun: `uv run pytest` from Orchestrator record, exit 0, `209 passed, 2 skipped in 142.65s`.
- `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf`, exit 0.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf --workers 4`, exit 1 after all 229 chunks completed and metrics merged; official JSON write failed with `OSError: [Errno 36] File name too long`.
- `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf --workers 4`, exit 1 after all 46 chunks completed and metrics merged; official JSON write failed with `OSError: [Errno 36] File name too long`.

Recovery commands used the repository's fixed metric aggregation functions on completed chunk outputs:

```bash
uv run python - <<'PY'
from pathlib import Path
from dynamaxx.eval.protocols import create_case
from dynamaxx.eval.runner import (
    _chunk_result_path,
    _evaluation_result_from_chunk_totals,
    _read_chunk_result,
    write_metric_csv,
    write_metric_json,
)

candidate = 'dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf'
history_path = Path('.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux')
run_path = Path('outputs/eval/runs') / f'iteration_{candidate}'
chunk_path = run_path / 'chunks'
case = create_case('iteration')
chunk_count = len(tuple(range(0, case.initial_times.size, 8)))
chunk_totals = tuple(
    _read_chunk_result(_chunk_result_path(chunk_path, index), expected_chunk_index=index)
    for index in range(chunk_count)
)
result = _evaluation_result_from_chunk_totals(case, chunk_totals)
write_metric_json(result, history_path / 'candidate_iteration_metrics_recovered.json')
write_metric_csv(result, history_path / 'candidate_iteration_metrics_recovered.csv')
PY
```

```bash
uv run python - <<'PY'
from pathlib import Path
from dynamaxx.eval.protocols import chunk_initial_count, create_case
from dynamaxx.eval.runner import (
    _chunk_result_path,
    _evaluation_result_from_chunk_totals,
    _read_chunk_result,
    write_metric_csv,
    write_metric_json,
)

candidate = 'dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf'
history_path = Path('.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux')
protocol = 'validation'
run_path = Path('outputs/eval/runs') / f'{protocol}_{candidate}'
chunk_path = run_path / 'chunks'
case = create_case(protocol)
chunk_size = chunk_initial_count(protocol)
chunk_count = len(tuple(range(0, case.initial_times.size, chunk_size)))
chunk_totals = tuple(
    _read_chunk_result(_chunk_result_path(chunk_path, index), expected_chunk_index=index)
    for index in range(chunk_count)
)
result = _evaluation_result_from_chunk_totals(case, chunk_totals)
write_metric_json(result, history_path / 'candidate_validation_metrics_recovered.json')
write_metric_csv(result, history_path / 'candidate_validation_metrics_recovered.csv')
PY
```

## Cache Reuse

- Iteration incumbent cache reused from `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface.json` and `.csv`. Checks: requested incumbent matched `.logbook/leaderboard.json`; data path, target variables, lead range, protocol inclusion, and `eval_code_commit` matched; artifact was readable; model name matched; primary was finite; 120 records; diagnostics clean; RMSE values finite.
- Validation incumbent cache reused from `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface.json` and `.csv`. Checks were the same as iteration, with protocol inclusion for validation.
- No incumbent evaluation commands were run. Candidate source edits were not treated as cache invalidation under `roles/SCORER.md`.

## Artifacts

- Candidate fast JSON/CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf.json`, `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf.csv`.
- Candidate iteration recovered JSON/CSV: `.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux/candidate_iteration_metrics_recovered.json`, `.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux/candidate_iteration_metrics_recovered.csv`.
- Candidate validation recovered JSON/CSV: `.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux/candidate_validation_metrics_recovered.json`, `.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux/candidate_validation_metrics_recovered.csv`.
- Raw candidate chunk directories: `outputs/eval/runs/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf`, `outputs/eval/runs/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf`.

## Measurement Lessons

- The candidate model name is long enough that official `iteration_*.json` and `validation_*.json` filenames exceed the filesystem component limit, even though the shorter `fast_*.json` filename fits. Future scorer or orchestrator setup should account for this before launching long runs for similarly long model names.
- The evaluation forecast chunks were usable despite the final CLI write failure because the fixed runner persists chunk totals before final aggregation. Recovery used the repository's existing metric conversion functions and did not alter metric definitions, target variables, lead times, or data splits.

## Anomalies

- Cache reuse: incumbent iteration and validation metrics were reused from leaderboard artifacts; no incumbent reruns.
- Resource limits: no resource failures observed. Pre-run checks showed 172 GiB available RAM and 4.1 TiB free disk.
- Failed or restarted commands: no restarts. Candidate iteration and validation commands exited 1 only at official metric JSON write due filename length after completing all chunks.
- Nonfinite or unstable outputs: none reported. Recovered candidate iteration and validation diagnostics had failed false with 0 issues, 120 records, and finite primary scores.

## Recommendation To Orchestrator

Report the measured gate status and the filename-length artifact anomaly. This Scorer report does not accept or reject the candidate.

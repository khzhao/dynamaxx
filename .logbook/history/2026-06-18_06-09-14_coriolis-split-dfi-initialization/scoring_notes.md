# Scoring Notes

## Gate Status

- Fast gate: passed. The scorer reran `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_dfi_coriolis`; exit status 0, failed=False, issues=0, primary_score=-1.0953607227965798.
- Iteration promotion gate: did not promote to validation. Candidate iteration primary_score=-1.1233009637594966 versus incumbent iteration primary_score=-1.1241936221835356, for iteration_delta=+0.0008926584240389612. This is below the required +0.002 threshold.
- Validation acceptance gate: not evaluated because candidate validation was not run under the promotion gate. The compatible incumbent validation score remains -1.1127999773519712.

## Measurement Lessons

- The DFI Coriolis split produced a small positive iteration primary-score delta, but it was less than half of the +0.002 validation-promotion threshold.
- Iteration diagnostics were clean for both candidate and incumbent: failed=False and issue_count=0.
- Guardrails were clean after filtering CSV rows by exact model_name. No early day 1-5 mean RMSE regression exceeded 2%, and no per-variable plus lead RMSE regression exceeded 10%.
- The worst single RMSE regression was mean_sea_level_pressure at 120 lead hours: candidate=1571.9936839528755, incumbent=1550.3690906878755, relative_delta=+0.01394802914666302.
- Early day 1-5 mean RMSE regressions below guardrail were geopotential_500 at +0.35046875281744224% and mean_sea_level_pressure at +0.3303352105164788%. Early day 1-5 mean RMSE improved for 10m_u_component_of_wind by -0.12057550050329057% and 2m_temperature by -0.08634699601157484%.

## Anomalies

- Cache reuse: candidate fast was rerun by Scorer, replacing the Implementer sanity artifact. Candidate iteration startup reported cached=0 and pending=229. Compatible incumbent iteration and validation artifacts were reused as provided by the Orchestrator.
- Resource limits: none observed. Candidate iteration used four GPU workers with effective_workers=4.
- Failed or restarted commands: no fixed eval command failed or restarted. A preliminary registry probe using `from dynamaxx.dycore.registry import list_models` exited 1 because that helper does not exist; the successful registry confirmation used `dycore_model_names()`.
- Nonfinite or unstable outputs: none reported by diagnostics or CLI output.

## Recommendation To Orchestrator

Report the measured gate status only: fast passed, iteration did not promote to validation, candidate validation was not run, and golden was not run.

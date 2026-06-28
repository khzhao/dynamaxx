# Scoring Notes

## Gate Status

- Registration: candidate `dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter` and incumbent `dinosaur_dfi_surface_residual_weak_hs_logp_init` are both registered.
- Full tests: `uv run pytest` passed with 116 passed and 2 skipped.
- Fast gate: reused `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter.json`; model and `case.name=fast` matched, diagnostics `failed=False`, issue count 0, primary score `-1.1901240466487215`.
- Iteration primary: candidate `-1.2050427252934939` versus incumbent `-1.2155220438349765`; delta `+0.010479318541482652`, passing the `+0.002` primary threshold.
- Iteration diagnostics: candidate diagnostics `failed=False`, issue count 0.
- Iteration early RMSE guardrail: failed. `10m_u_component_of_wind` mean RMSE over leads 24..120 h regressed from `9.252510608236614` to `9.447076530321109`, relative regression `0.021028446258823053`, above the `0.02` limit.
- Iteration variable+lead RMSE guardrail: passed. Worst point regression was `10m_u_component_of_wind` at 240 h, from `14.67085779429217` to `15.311408375212949`, relative regression `0.04366142661201389`, below the `0.10` limit.
- Iteration promotion gate: does not promote to validation because the early mean wind RMSE guardrail fails.
- Validation was measured but was not gate-authorized after the corrected iteration guardrail calculation. Candidate validation primary was `-1.1935304093217602` versus incumbent `-1.2028991078287248`, delta `+0.009368698506964535`; diagnostics were clean, but `10m_u_component_of_wind` early mean RMSE regressed by `0.02062364835708408`, above the `0.02` limit.

## Command Details

- `uv run python -c "... dycore_model_names ..."` exited 0 and confirmed both models are registered.
- `uv run pytest` exited 0: 116 passed, 2 skipped in 59.59s.
- Candidate fast artifact verification exited 0 and reused the existing fast JSON/CSV.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter --workers 4` exited 0. It ran 229 chunks from scratch with `cached=0`, used 4 GPU workers, and wrote `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter.json`.
- `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter --workers 4` exited 0. It ran 46 chunks from scratch with `cached=0`, used 4 GPU workers, and wrote `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter.json`.
- Golden was not run.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter.csv`
- Candidate validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter.json`
- Candidate validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_thermal_recenter.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init.csv`
- Incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init.json`
- Incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init.csv`

## Measurement Lessons

- Metrics JSON files include both evaluated-model records and persistence records. Guardrail comparisons must filter records by `model_name` before joining by `channel_name` and `lead_hours`.
- The candidate improves primary score and early 2m temperature RMSE, but consistently worsens 10m wind RMSE by just over the early-lead 2% guardrail.
- The validation measurement shows the same early wind RMSE pattern as iteration, so future proposals around thermal recentering should check low-level wind response before full scoring.

## Anomalies

- Cache reuse: incumbent iteration and validation artifacts were reused as requested; candidate fast artifact was reused after verification; candidate iteration and validation were run from scratch with `cached=0`.
- Resource limits: no resource failures observed; both long evals dispatched to 4 GPU workers.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by diagnostics.
- Scoring anomaly: validation was run after an initial guardrail check accidentally compared persistence rows because the metric JSON contains duplicate `channel_name`/`lead_hours` pairs for the evaluated model and persistence. The corrected calculation excludes persistence records and shows the iteration promotion gate fails, so the validation run should be treated as measured but not gate-authorized.

## Recommendation To Orchestrator

Report the measured gate status and caveat above. The Scorer is not accepting or rejecting the candidate.

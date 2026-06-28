# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate fast artifacts were diagnostic-clean with primary score -1.337193838597716.
- Iteration promotion gate: failed. Candidate iteration primary score -1.376430535805006 was below incumbent -1.325188435151175; delta -0.051242100653831, required at least +0.002000000000000. Early-lead mean RMSE also regressed by 3.646456% for 10m_u_component_of_wind, above the 2% limit.
- Validation acceptance gate: not evaluated. Candidate validation was not run because the iteration promotion gate failed.

## Measurement Lessons

- The scale-selective hyperdiffusion candidate was diagnostic-clean but reduced the iteration primary score and worsened early 10m zonal wind RMSE. Future proposals should avoid increasing damping in a way that harms low-level wind evolution at short leads, or should tune any diffusion strength with the 1-5 day wind gate in mind before iteration scoring.
- No variable+lead RMSE regression exceeded the 10% limit; the promotion failure was driven by primary score and the early-wind mean RMSE gate.

## Anomalies

- Cache reuse: none for candidate iteration. The Scorer found no pre-existing iteration_dinosaur_hyperdiffusion run files before launch, and the evaluator reported cached=0 pending=229.
- Resource limits: none observed. The fixed iteration command used 4 GPU workers and completed with exit status 0.
- Failed or restarted commands: none observed during Scorer execution.
- Nonfinite or unstable outputs: none reported by diagnostics; candidate iteration diagnostics failed=false, issues=0.

## Recommendation To Orchestrator

Report that the candidate did not promote to validation under the iteration gate. The Orchestrator should make the terminal decision using the failed primary-score gate and the 10m_u_component_of_wind early-lead RMSE regression; no candidate validation evidence was produced.

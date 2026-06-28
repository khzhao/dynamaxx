# Scoring Notes

## Gate Status

- Fast gate: passed artifact verification. `outputs/eval/fast_dinosaur_dfi_pressure_grid.json` has `failed=false`, 0 diagnostic issues, 120 records, and primary score `-1.4026822509855363`.
- Iteration promotion gate: failed. Candidate `dinosaur_dfi_pressure_grid` primary score was `-1.4240296998737416`; incumbent `dinosaur_dfi` primary score was `-1.3208025947740873`; delta was `-0.10322710509965427`, below the required `+0.002` threshold. Candidate diagnostics were clean. No target variable had mean RMSE regression over leads 1-5 days above 2%, and no target variable+lead RMSE regression exceeded 10%.
- Validation acceptance gate: not run by protocol because the iteration promotion gate failed.

## Measurement Lessons

- The pressure-aware sigma grid was numerically stable enough to pass fast and iteration diagnostics, but it severely degraded the aggregate primary score relative to the accepted `dinosaur_dfi` incumbent.
- The fixed target-variable RMSE guardrails were only roundoff-scale, so the large primary degradation likely entered through non-guardrail metric components or variables in the fixed aggregate. Future vertical-coordinate ideas should inspect complete metric components before assuming guardrail neutrality implies aggregate neutrality.
- Matching sigma interfaces to input pressure levels removed useful behavior from the equidistant grid under this adapter. The accepted DFI incumbent should retain its current vertical grid.

## Anomalies

- Cache reuse: incumbent iteration and validation artifacts were reused from the accepted leaderboard state. Candidate fast artifacts were produced by the Implementer and verified. Candidate iteration artifact was freshly produced for `dinosaur_dfi_pressure_grid`.
- Resource limits: no memory, GPU, disk, or worker-limit issue was observed from the produced artifacts. GPUs were idle after the candidate iteration artifact finished.
- Failed or restarted commands: the delegated Scorer produced `outputs/eval/iteration_dinosaur_dfi_pressure_grid.*` but did not write logbook scoring files before becoming unresponsive; the Orchestrator closed that delegate and wrote the score artifacts from the completed fixed output. No validation command was run.
- Nonfinite or unstable outputs: none observed. Candidate fast and iteration diagnostics were clean with 0 issues.

## Recommendation To Orchestrator

Report the measured gate status as rejected by the iteration primary-score threshold. Do not run validation and do not update the leaderboard for this candidate.

# Scoring Notes

## Gate Status

- Fast gate: passed artifact verification. `outputs/eval/fast_dinosaur_dfi_ref_profile.json` has `failed=false`, 0 diagnostic issues, 120 records, and primary score `-1.2826846667797114`.
- Iteration promotion gate: failed. Candidate `dinosaur_dfi_ref_profile` primary score was `-1.3205664654977811`; incumbent `dinosaur_dfi` primary score was `-1.3208025947740873`; delta was `+0.00023612927630622949`, below the required `+0.002` threshold. Candidate diagnostics were clean. No target variable had mean RMSE regression over leads 1-5 days above 2%, and no target variable+lead RMSE regression exceeded 10%.
- Validation acceptance gate: not run by protocol because the iteration promotion gate failed.

## Measurement Lessons

- The fixed standard-atmosphere reference profile was numerically clean and preserved the accepted DFI path, but it produced only a sub-threshold primary-score gain over `dinosaur_dfi`.
- Target-variable RMSE differences were roundoff-scale across the checked WeatherBench2 target variables and leads. The small primary movement is not enough evidence to promote this numerical split change.
- Future balance proposals should either target a larger physical inconsistency or include pre-implementation diagnostics showing that the proposed split affects the fixed target metrics beyond roundoff-scale RMSE movement.

## Anomalies

- Cache reuse: incumbent iteration and validation artifacts were reused from the accepted leaderboard state. Candidate fast artifacts were produced by the Implementer and verified. Candidate iteration artifact was freshly produced for `dinosaur_dfi_ref_profile`.
- Resource limits: no memory, GPU, disk, or worker-limit issue was observed from the produced artifacts. GPUs were idle after the candidate iteration artifact finished.
- Failed or restarted commands: the delegated Scorer produced `outputs/eval/iteration_dinosaur_dfi_ref_profile.*` but did not write logbook scoring files before becoming unresponsive; the Orchestrator closed that delegate and wrote the score artifacts from the completed fixed output. No validation command was run.
- Nonfinite or unstable outputs: none observed. Candidate fast and iteration diagnostics were clean with 0 issues.

## Recommendation To Orchestrator

Report the measured gate status as rejected by the iteration primary-score threshold. Do not run validation and do not update the leaderboard for this candidate.

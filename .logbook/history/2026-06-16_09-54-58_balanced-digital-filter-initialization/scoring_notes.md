# Scoring Notes

## Gate Status

- Fast gate: passed artifact verification. `outputs/eval/fast_dinosaur_dfi.json` has `failed=false`, 0 diagnostic issues, 120 records, and primary score `-1.2844866682514346`.
- Iteration promotion gate: passed. Candidate `dinosaur_dfi` primary score was `-1.3208025947740873`; incumbent `dinosaur` primary score was `-1.3251884351511753`; delta was `+0.004385840377088002`, above the `+0.002` threshold. Candidate diagnostics were clean. No target variable had mean RMSE regression over leads 1-5 days above 2%, and no target variable+lead RMSE regression exceeded 10%.
- Validation acceptance gate: measured as passed. Candidate `dinosaur_dfi` primary score was `-1.308334010223954`; incumbent `dinosaur` primary score was `-1.3128324262513928`; delta was `+0.004498416027438834`, above the `+0.001` threshold. Candidate diagnostics were clean, no early-lead mean RMSE regression exceeded 2%, and no diagnostic notes indicated an obvious nonphysical failure mode.

## Measurement Lessons

- The RMSE guardrails show only roundoff-scale candidate-versus-incumbent differences for the checked target variables and leads, while the primary score improves on both iteration and validation. Future analysis should inspect the primary-score components if the Orchestrator wants to understand where the measured gain enters.
- The fixed evaluation path handled `dinosaur_dfi` with four GPU workers without scorer-side intervention, restarts, nonfinite diagnostics, or resource-limit behavior.

## Anomalies

- Cache reuse: candidate iteration and validation were fresh runs with evaluator-reported `cached=0`. Compatible incumbent iteration and validation artifacts were reused from `outputs/eval/iteration_dinosaur.*` and `outputs/eval/validation_dinosaur.*`. Candidate fast artifacts were reused from the Implementer-provided fast run and verified by Scorer.
- Resource limits: none observed during Scorer runs.
- Failed or restarted commands: none during Scorer runs. The Implementer reported an earlier interrupted no-jit DFI unit test and a recursion repair before final passing tests and fast evaluation.
- Nonfinite or unstable outputs: none observed. Candidate and incumbent diagnostic artifacts were clean with 0 issues.

## Recommendation To Orchestrator

Report the measured gate status as passing for both iteration promotion and validation acceptance. The Scorer does not accept or reject; the Orchestrator should make the final decision and update or preserve leaderboard state accordingly.

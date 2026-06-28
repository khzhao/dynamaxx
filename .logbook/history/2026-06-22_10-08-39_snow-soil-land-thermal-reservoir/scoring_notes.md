# Scoring Notes

## Gate Status

- Fast gate: passed from the existing candidate artifact. `uv run dynamaxx-eval fast --model dino_land_soilflux` is recorded in `implementation.md` with exit status 0, and I verified `outputs/eval/fast_dino_land_soilflux.json` has `failed=false`, 0 issues, 120 records, and primary score -0.4416749415172102.
- Iteration promotion gate: did not promote. Candidate iteration primary score was -0.4270112877010464; cached incumbent iteration primary score was -0.4270118753609274; delta was 5.876598810350409e-07, below the required +0.002.
- Iteration diagnostics and RMSE guardrails: diagnostics were clean. Guardrails compare candidate-model rows against incumbent-model rows and exclude persistence baseline rows. Early day 1-5 mean RMSE regressions were all <= 2%, and the worst variable+lead RMSE regression was 0.001108882523514213% at 10 m zonal wind lead 240 h, below the 10% limit.
- Validation acceptance gate: not evaluated. The candidate validation command was not run because validation is allowed only after the iteration promotion gate passes.

## Cache Reuse

- Iteration incumbent metrics were reused from leaderboard artifacts: `outputs/eval/iteration_ocean_bulk_sensible_heat_flux.json` and `outputs/eval/iteration_ocean_bulk_sensible_heat_flux.csv`. No incumbent rerun was performed.
- The reuse checks passed: requested incumbent matched `.logbook/leaderboard.json`, fingerprint data path/target variables/lead days/protocol/eval code commit matched, current HEAD was `329dd5758204b7e77f1abb258b1dab9ee5d9b2c8`, current candidate diff did not touch fixed evaluation code, artifacts were readable, primary score was finite, and incumbent model guardrail records were present.
- Validation incumbent artifacts `outputs/eval/validation_ocean_bulk_sensible_heat_flux.json` and `outputs/eval/validation_ocean_bulk_sensible_heat_flux.csv` were checked and valid for reuse, but they were not used in a candidate comparison because candidate validation did not run.
- Candidate source edits were not treated as incumbent cache invalidation, consistent with `roles/SCORER.md`.

## Measurement Lessons

- The candidate is numerically almost indistinguishable from the incumbent on iteration primary score, with delta 5.876598810350409e-07.
- The additional land soil/snow reservoir did not trigger meaningful RMSE guardrail regressions; the limiting factor is lack of primary-score improvement.

## Anomalies

- Cache reuse: no anomalies.
- Resource limits: no anomalies reported by the evaluator.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported; candidate fast and iteration diagnostics were clean.

## Recommendation To Orchestrator

Return to Orchestrator for the candidate decision. Do not run validation or golden for this candidate state under the fixed gate rules.

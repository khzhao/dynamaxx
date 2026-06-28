# Scoring Notes

## Gate Status

- Fast gate: failed. `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_no_vadv` exited `0`, but the verified artifact reports `diagnostics.failed=true`.
- Iteration promotion gate: not run. The protocol forbids iteration after a failed fast gate.
- Validation acceptance gate: not run. Validation is allowed only after iteration promotion.

## Command Record

- Registration check: `uv run python - <<'PY' ... create_dycore_model(...) ... PY`, exit `0`.
- Artifact verification: `uv run python - <<'PY' ... inspect outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_no_vadv.json ... PY`, exit `0`.
- Implementer-provided checks were accepted as the test record: compileall exit `0`, ruff format stable after formatting one file, ruff check exit `0` after import-order repair, focused pytest `41 passed`, full pytest `107 passed, 2 skipped`, and `git diff --check` exit `0`.
- Implementer-provided fast command: `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_no_vadv`, exit `0`, artifact verified by the Scorer.

## Fast Artifact Verification

- Artifact: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_no_vadv.json`.
- Exact candidate row count: `60`.
- Persistence row count: `60`.
- Candidate primary score in the raw artifact: `-Infinity`; `scores.json` encodes this as `-1.7976931348623157e308` to remain valid JSON and records the raw representation separately.
- Diagnostic issue codes: `nonfinite_forecast`, `nonfinite_metric`.
- Earliest nonfinite candidate metric lead: `264` hours.
- Variables nonfinite at the earliest lead: `2m_temperature`, `mean_sea_level_pressure`, `geopotential_500`, and `10m_u_component_of_wind`.
- Nonfinite metric fields at the earliest lead: `rmse`, `mae`, `bias`, and `skill_vs_persistence`.

## Measurement Lessons

- Disabling explicit vertical advection is unstable under the fast gate for this incumbent configuration. The forecast remains finite through lead hour `240`, then all four target variables become nonfinite in the metric records from lead hour `264` onward.
- This result falsifies the bounded ablation before iteration scoring. Future proposals should treat vertical-transport removal as a stability risk unless paired with a separately reviewed infrastructure or dynamics change; it should not be tuned inside this candidate.

## Anomalies

- Cache reuse: compatible incumbent iteration and validation artifacts were referenced from the leaderboard only. No incumbent evaluation was rerun.
- Resource limits: none observed during Scorer verification.
- Failed or restarted commands: no Scorer commands failed. The Implementer reported one ruff import-order failure that was repaired before scoring.
- Nonfinite or unstable outputs: fast diagnostics found nonfinite forecast values and nonfinite metric records for the candidate.

## Recommendation To Orchestrator

Report that the candidate failed the fast gate and that iteration, validation, and golden were correctly skipped. The Scorer does not accept or reject the candidate.

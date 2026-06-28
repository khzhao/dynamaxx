# Scoring Notes

## Gate Status

- Fast gate: failed. The candidate fast command exited `0`, but the fixed diagnostics reported `nonfinite_forecast` and `nonfinite_metric`.
- Iteration promotion gate: not run. Protocol forbids iteration after a failed fast gate.
- Validation acceptance gate: not run. Validation is only allowed after iteration promotion.

## Command Record

- Implementer-provided checks were accepted as the candidate test record: `compileall` passed, `ruff format` exited `0` and reformatted one file, `ruff check` passed, focused pytest passed with `42 passed`, full pytest passed with `108 passed, 2 skipped`, and `git diff --check` passed.
- Implementer-provided fast command: `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_t120`, exit `0`.
- Scorer registration check: `create_dycore_model("dinosaur_dfi_surface_residual_weak_hs_t120")` and `create_dycore_model("dinosaur_dfi_surface_residual_weak_hs")` both succeeded through `dynamaxx.dycore.registry`.
- Scorer artifact verification used exact `model_name` filtering on `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_t120.json`.
- Incumbent reference artifacts were read only from `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs.json` and `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs.json`. No incumbent evaluation was run.

## Artifact Verification

- Candidate fast artifact: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_t120.json`.
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_t120.csv`.
- Exact-filtered candidate rows: `60`.
- Exact-filtered persistence rows: `60`.
- Raw fast primary score in the artifact: `-Infinity`. `scores.json` stores `-1.7976931348623157e308` as a strict-JSON finite sentinel and records the raw value separately.
- Earliest nonfinite candidate metric lead: `24` hours.
- Earliest affected variables: `2m_temperature`, `mean_sea_level_pressure`, `geopotential_500`, and `10m_u_component_of_wind`.
- Nonfinite metric fields at the earliest lead: `rmse`, `mae`, `bias`, and `skill_vs_persistence`.

## Measurement Lessons

- The fixed T120 truncation candidate is unstable under the existing 900 second step, DFI setup, weak Held-Suarez forcing, near-surface residual correction, and diffusion settings.
- Because nonfinite metrics appear at the first scored lead for every target variable, this result does not support a bounded revision inside the same proposal without adding a separate stabilizing change.
- Future resolution proposals should include stability reasoning for the transform grid, diffusion strength, and step size before spending iteration or validation budget.

## Anomalies

- Cache reuse: only compatible incumbent iteration and validation artifacts were reused for reference.
- Resource limits: none observed by the Scorer; no long evaluation was started.
- Failed or restarted commands: one initial registration probe used a helper name that does not exist in this repository and exited `1`; the successful repository API check used `dycore_model_names()` and `create_dycore_model()`.
- Nonfinite or unstable outputs: the candidate fast artifact reported `nonfinite_forecast` and `nonfinite_metric`; all exact-filtered candidate metric rows are nonfinite.

## Recommendation To Orchestrator

Report the measured fast-gate failure and do not promote this candidate to iteration or validation. The Scorer does not accept or reject candidates.

# Scoring Notes

## Gate Status

- Fast gate: passed by provided `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_mass_residual` exit 0 record and Scorer artifact verification. Fast primary score was `-1.2470991177529807`; diagnostics failed `false`, issue count `0`.
- Iteration promotion gate: failed on primary-score margin. Candidate `-1.284988567046514` versus incumbent `-1.2854136202685928`, delta `0.00042505322207886387`; required delta was `0.002`.
- Iteration diagnostics gate: passed. Candidate diagnostics failed `false`, issue count `0`; incumbent diagnostics failed `false`, issue count `0`.
- Iteration early RMSE guardrail: passed. No variable had day 1-5 mean RMSE regression above `2%`.
- Iteration variable+lead RMSE guardrail: passed. No variable+lead RMSE regression exceeded `10%`; global max was mean sea level pressure at lead 144 h with relative regression `4.2353923213160284e-05`.
- Validation acceptance gate: not run. Validation was allowed only if candidate passed the iteration promotion gate.

## Exact Commands And Exits

- `uv run python - <<'PY' ... dycore_model_names registration check ... PY`: exit `0`; confirmed `dinosaur_dfi_surface_mass_residual` and `dinosaur_dfi_surface_residual` are registered.
- `uv run pytest`: exit `0` from Orchestrator-provided passing record, not rerun by Scorer; reported `102 passed, 2 skipped`.
- `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_mass_residual`: exit `0` from Orchestrator-provided passing record, not rerun by Scorer.
- `uv run python - <<'PY' ... fast artifact verification ... PY`: exit `0`; verified `outputs/eval/fast_dinosaur_dfi_surface_mass_residual.json` has exact candidate `model_name`, clean diagnostics, and primary score `-1.2470991177529807`.
- `nproc && free -h && df -h . outputs/eval .logbook`: exit `0`; observed 48 CPUs, 175 GiB available RAM, and 4.1 TiB free disk.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_mass_residual --workers 4`: exit `0`; wrote `outputs/eval/iteration_dinosaur_dfi_surface_mass_residual.json` and `.csv`.
- `uv run python - <<'PY' ... filtered candidate/incumbent comparison ... PY`: exit `0`; computed primary deltas and RMSE guardrails using exact `model_name` filters.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_mass_residual.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_mass_residual.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_mass_residual.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_mass_residual.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual.csv`
- Incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual.json`
- Incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual.csv`
- Candidate validation JSON/CSV: not produced because iteration promotion gate failed.

## RMSE Guardrails

Day 1-5 mean RMSE regressions:

| variable | candidate mean RMSE | incumbent mean RMSE | relative regression | gate |
|---|---:|---:|---:|---|
| `10m_u_component_of_wind` | 9.191501155496947 | 9.191500982911077 | 1.877667980982714e-08 | pass |
| `2m_temperature` | 7.807050708472215 | 7.807050586677929 | 1.5600550464457382e-08 | pass |
| `geopotential_500` | 764.5017376496944 | 766.5217952826715 | -0.0026353557660185956 | pass |
| `mean_sea_level_pressure` | 1056.4650701379849 | 1057.7060920239628 | -0.0011733144919333861 | pass |

Per-variable maximum lead RMSE regressions:

| variable | lead hours | candidate RMSE | incumbent RMSE | relative regression | gate |
|---|---:|---:|---:|---:|---|
| `10m_u_component_of_wind` | 312 | 14.645534984209284 | 14.645527556439532 | 5.071698321232043e-07 | pass |
| `2m_temperature` | 96 | 9.66877974678154 | 9.668779436077765 | 3.213474644352434e-08 | pass |
| `geopotential_500` | 360 | 2163.5769933960482 | 2163.5952734093744 | -8.448906110495681e-06 | pass |
| `mean_sea_level_pressure` | 144 | 1859.462137073888 | 1859.3833848927804 | 4.2353923213160284e-05 | pass |

## Anomalies

- Cache reuse: candidate iteration reported `cached=0`, `pending=229`; no candidate iteration cache reuse.
- Incumbent cache/artifact reuse: reused compatible incumbent iteration and validation artifacts from `.logbook/leaderboard.json` as directed by the Orchestrator.
- Resource limits: none observed. Requested workers `4`; run reported effective workers `4`, GPU count `4`, worker devices `0:0,1:1,2:2,3:3`.
- Failed or restarted commands: none observed by Scorer.
- Nonfinite or unstable outputs: none reported; candidate iteration diagnostics were clean.

## Measurement Lessons

- Iteration JSON records include persistence rows, so scorer comparisons must filter records by exact `model_name` for both candidate and incumbent.
- The mass diagnostic residual candidate changed RMSEs only at tiny magnitudes relative to the incumbent. This was clean by guardrails, but not large enough for the primary-score promotion threshold.
- Validation should remain gated behind iteration primary-score improvement; otherwise low-signal candidates can consume validation resources despite clean diagnostics.

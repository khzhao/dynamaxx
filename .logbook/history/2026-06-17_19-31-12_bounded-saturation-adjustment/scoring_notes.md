# Scoring Notes

## Scope

- Candidate: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust`
- Incumbent: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`
- History directory: `.logbook/history/2026-06-17_19-31-12_bounded-saturation-adjustment`
- Worker count: `4`

## Commands

| Command | Exit status | Notes |
| --- | ---: | --- |
| `uv run python - <<'PY' ... dycore_model_names ... PY` | 0 | Confirmed candidate and incumbent are registered using `dynamaxx.dycore.registry.dycore_model_names()`. |
| `git rev-parse HEAD` | 0 | Evaluated source commit `a7833574e9ade1a5271bd8cbef2fa1357465f5a8`. |
| `uv run pytest` | 0 | `132 passed, 2 skipped in 68.37s`. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust` | 0 | Completed cleanly: `failed=False`, `issues=0`, primary `-1.1339683809399665`. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust --workers 4` | 0 | Completed 229 chunks with `cached=0`; `failed=False`, `issues=0`, primary `-1.1703668264356009`. |
| `uv run python - <<'PY' ... exact-model CSV guardrail comparison ... PY` | 0 | Computed iteration deltas and guardrails after filtering candidate and incumbent rows by exact `model_name`. |

Validation was not run because the fixed iteration promotion gate did not pass. Golden was not run.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_sat_adjust.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`
- Incumbent validation JSON available for reuse: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Incumbent validation CSV available for reuse: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`

## Scores

- Fast candidate primary: `-1.1339683809399665`
- Iteration candidate primary: `-1.1703668264356009`
- Iteration incumbent primary: `-1.143975258592661`
- Iteration primary delta: `-0.026391567842939834`
- Required iteration primary delta: `>= +0.002`
- Validation incumbent primary available for reuse: `-1.1301883620649706`

## Diagnostics

- Candidate fast: `failed=False`, `issues=0`
- Candidate iteration: `failed=False`, `issues=0`
- Incumbent iteration: `failed=False`, `issues=0`
- Incumbent validation artifact: `failed=False`, `issues=0`

## Guardrails

All iteration comparisons filtered records by exact `model_name`; both candidate and incumbent had `60` exact-model metric rows.

- Primary delta gate: failed; delta was `-0.026391567842939834`, below `+0.002`.
- Diagnostics gate: passed; candidate iteration diagnostics were clean.
- Day 1-5 mean RMSE by target variable:
  - `2m_temperature`: candidate `7.30861480626073`, incumbent `7.358666285692398`, relative regression `-0.006801705293931391`.
  - `mean_sea_level_pressure`: candidate `1051.8106875813464`, incumbent `1012.9263924182685`, relative regression `0.03838807583070794`.
  - `geopotential_500`: candidate `772.8146453853643`, incumbent `746.8278674886182`, relative regression `0.03479620810633745`.
  - `10m_u_component_of_wind`: candidate `8.974082592872831`, incumbent `8.67161758555166`, relative regression `0.034879883059549054`.
- Target-variable day 1-5 mean RMSE regressions over 2%: `mean_sea_level_pressure`, `geopotential_500`, and `10m_u_component_of_wind`.
- Worst variable+lead RMSE regression: `geopotential_500` at `288` hours, candidate `2128.95935811874`, incumbent `2003.1469100552672`, relative regression `0.06280739941335689`.
- Variable+lead RMSE regressions over 10%: none.

## Gate Status

- Fast gate: passed.
- Iteration promotion gate: failed.
- Validation acceptance gate: not run because iteration did not promote.

## Anomalies And Lessons

- Candidate fast artifacts existed before scoring, but the Scorer reran the official fast command and confirmed clean diagnostics.
- Candidate iteration started with `cached=0` and completed 229 chunks under the requested `--workers 4`.
- The bounded saturation adjustment kept diagnostics clean but lowered the iteration primary score versus the incumbent.
- The decisive iteration blockers were the negative primary delta and early lead mean RMSE regressions above 2% for three target variables.
- No individual target variable plus lead RMSE regression exceeded 10%; the worst was `geopotential_500` at `288` hours with `0.06280739941335689` relative regression.

## Recommendation To Orchestrator

Report the measured gate status and caveats above. This scorer record does not accept or reject the candidate.

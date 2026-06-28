# Scoring Notes

## Scope

- Candidate: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_continuity_balanced`
- Incumbent: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`
- History directory: `.logbook/history/2026-06-17_22-19-32_continuity-balanced-divergence-init`
- Worker count: `4`

## Commands

| Command | Exit status | Notes |
| --- | ---: | --- |
| `uv run python - <<'PY' ... dycore_model_names ... PY` | 0 | Confirmed candidate and incumbent are registered using `dynamaxx.dycore.registry.dycore_model_names()`. |
| `git rev-parse HEAD` | 0 | Evaluated source commit `a7833574e9ade1a5271bd8cbef2fa1357465f5a8`. |
| `git status --short` | 0 | Candidate changes were present before scoring in dycore and test files. |
| `uv run pytest` | 0 | `130 passed, 2 skipped in 64.81s`. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_continuity_balanced` | 0 | Reran cleanly: `failed=False`, `issues=0`, primary `-1.1241672381984182`. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_continuity_balanced --workers 4` | 0 | Completed 229 chunks with `cached=0`; `failed=False`, `issues=0`, primary `-1.1452881585043542`. |
| `python - <<'PY' ... exact-model CSV guardrail comparison ... PY` | 0 | Computed iteration deltas and guardrails after filtering candidate and incumbent rows by exact `model_name`. |

Validation was not run because the fixed iteration promotion gate did not pass. Golden was not run.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_continuity_balanced.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_continuity_balanced.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_continuity_balanced.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_continuity_balanced.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`
- Incumbent validation JSON available for reuse: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Incumbent validation CSV available for reuse: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`

## Scores

- Fast candidate primary: `-1.1241672381984182`
- Iteration candidate primary: `-1.1452881585043542`
- Iteration incumbent primary: `-1.143975258592661`
- Iteration primary delta: `-0.001312899911693144`
- Required iteration primary delta: `>= +0.002`
- Validation incumbent primary available for reuse: `-1.1301883620649706`

## Diagnostics

- Candidate fast: `failed=False`, `issues=0`
- Candidate iteration: `failed=False`, `issues=0`
- Incumbent iteration: `failed=False`, `issues=0`
- Incumbent validation artifact: `failed=False`, `issues=0`

## Guardrails

All iteration comparisons filtered records by exact `model_name`; both candidate and incumbent had `60` exact-model metric rows.

- Primary delta gate: failed; delta was `-0.001312899911693144`, below `+0.002`.
- Diagnostics gate: passed; candidate iteration diagnostics were clean.
- Day 1-5 mean RMSE by target variable:
  - `10m_u_component_of_wind`: candidate `8.671541677974208`, incumbent `8.67161758555166`, relative regression `-0.000008753566068065817`.
  - `2m_temperature`: candidate `7.362501315435123`, incumbent `7.358666285692398`, relative regression `0.0005211582634453378`.
  - `geopotential_500`: candidate `745.7047451107895`, incumbent `746.8278674886182`, relative regression `-0.0015038570823627424`.
  - `mean_sea_level_pressure`: candidate `1011.7460077907382`, incumbent `1012.9263924182685`, relative regression `-0.0011653212280432897`.
- Target-variable day 1-5 mean RMSE regressions over 2%: none.
- Worst day 1-5 target-variable mean RMSE regression: `2m_temperature`, relative regression `0.0005211582634453378`.
- Worst variable+lead RMSE regression: `geopotential_500` at `24` hours, candidate `267.4221382266082`, incumbent `263.8712637418557`, relative regression `0.0134568441989434`.
- Variable+lead RMSE regressions over 10%: none.

## Gate Status

- Fast gate: passed.
- Iteration promotion gate: failed.
- Validation acceptance gate: not run because iteration did not promote.

## Anomalies And Lessons

- Candidate fast artifacts existed before scoring, but the Scorer reran the official fast command and confirmed clean diagnostics.
- Candidate iteration started with `cached=0` and completed 229 chunks under the requested `--workers 4`.
- The candidate produced clean diagnostics, and all fixed RMSE guardrails passed.
- The candidate regressed the iteration primary score relative to the incumbent, so it did not meet the fixed promotion threshold.
- Exact `model_name` filtering matters because the raw CSV artifacts include `persistence` rows alongside the evaluated model rows.
- Early day 1-5 mean RMSE improved for pressure and 500 hPa geopotential, but this did not translate into an overall primary-score improvement.

## Recommendation To Orchestrator

Report the measured gate status and caveats above. This scorer record does not accept or reject the candidate.

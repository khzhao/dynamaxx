# Scoring Notes

## Scope

- Candidate: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_tendency_dealias`
- Incumbent: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`
- History directory: `.logbook/history/2026-06-17_21-16-05_nonlinear-tendency-exponential-dealiasing`
- Worker count: `4`

## Commands

| Command | Exit status | Notes |
| --- | ---: | --- |
| `uv run python - <<'PY' ... dycore_model_names ... PY` | 0 | Confirmed candidate and incumbent are registered using `dynamaxx.dycore.registry.dycore_model_names()`. |
| `git rev-parse HEAD` | 0 | Evaluated source commit `a7833574e9ade1a5271bd8cbef2fa1357465f5a8`. |
| `git status --short` | 0 | Candidate changes were present before scoring in dycore and test files. |
| `uv run pytest` | 0 | `128 passed, 2 skipped in 64.59s`. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_tendency_dealias` | 0 | Reran cleanly: `failed=False`, `issues=0`, primary `-1.1182607015496349`. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_tendency_dealias --workers 4` | 0 | Completed 229 chunks with `cached=0`; `failed=False`, `issues=0`, primary `-1.1431871366924837`. |
| `python - <<'PY' ... exact-model CSV guardrail comparison ... PY` | 0 | Computed iteration deltas and guardrails after filtering candidate and incumbent rows by exact `model_name`. |

Validation was not run because the fixed iteration promotion gate did not pass. Golden was not run.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_tendency_dealias.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_tendency_dealias.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_tendency_dealias.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_tendency_dealias.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`
- Incumbent validation JSON available for reuse: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Incumbent validation CSV available for reuse: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`

## Scores

- Fast candidate primary: `-1.1182607015496349`
- Iteration candidate primary: `-1.1431871366924837`
- Iteration incumbent primary: `-1.143975258592661`
- Iteration primary delta: `0.0007881219001772966`
- Required iteration primary delta: `>= +0.002`
- Validation incumbent primary available for reuse: `-1.1301883620649706`

## Diagnostics

- Candidate fast: `failed=False`, `issues=0`
- Candidate iteration: `failed=False`, `issues=0`
- Incumbent iteration: `failed=False`, `issues=0`
- Incumbent validation artifact: `failed=False`, `issues=0`

## Guardrails

All iteration comparisons filtered records by exact `model_name`; both candidate and incumbent had `60` exact-model metric rows.

- Primary delta gate: failed; delta was `0.0007881219001772966`, below `+0.002`.
- Diagnostics gate: passed; candidate iteration diagnostics were clean.
- Day 1-5 mean RMSE by target variable:
  - `10m_u_component_of_wind`: candidate `8.668693304201678`, incumbent `8.67161758555166`, relative regression `-0.0003372244360560845`.
  - `2m_temperature`: candidate `7.357780135304617`, incumbent `7.358666285692398`, relative regression `-0.00012042268984310341`.
  - `geopotential_500`: candidate `746.6050548195537`, incumbent `746.8278674886182`, relative regression `-0.00029834541366763616`.
  - `mean_sea_level_pressure`: candidate `1012.5896974319692`, incumbent `1012.9263924182685`, relative regression `-0.00033239827574786245`.
- Target-variable day 1-5 mean RMSE regressions over 2%: none.
- Worst day 1-5 target-variable mean RMSE regression: `2m_temperature`, relative regression `-0.00012042268984310341`.
- Worst variable+lead RMSE regression: `2m_temperature` at `312` hours, candidate `10.370661366183807`, incumbent `10.36802023255296`, relative regression `0.00025473847191722303`.
- Variable+lead RMSE regressions over 10%: none.

## Gate Status

- Fast gate: passed.
- Iteration promotion gate: failed.
- Validation acceptance gate: not run because iteration did not promote.

## Anomalies And Lessons

- Candidate fast artifacts existed before scoring, but the Scorer reran the official fast command and confirmed clean diagnostics.
- Candidate iteration started with `cached=0` and completed 229 chunks under the requested `--workers 4`.
- The candidate produced clean diagnostics and a small positive iteration primary delta, but the delta was below the fixed promotion threshold.
- Early day 1-5 mean RMSE guardrails all passed, and no individual target variable plus lead RMSE regression exceeded 10%.
- Exact `model_name` filtering matters because the raw CSV artifacts include `persistence` rows alongside the evaluated model rows.

## Recommendation To Orchestrator

Report the measured gate status and caveats above. This scorer record does not accept or reject the candidate.

# Scoring Notes: mass-neutral-clipped-wtg-dse

## Commands And Status

| Command | Status | Notes |
| --- | ---: | --- |
| `targeted WTG tests` | 0 | Recorded from Orchestrator: `8 passed, 126 deselected in 63.74s`; not rerun by Scorer. |
| `uv run pytest` | 0 | Recorded from Orchestrator: `249 passed, 2 skipped in 246.32s`; not rerun by Scorer. |
| `uv run python - <<'PY' ... create_dycore_model, dycore_model_names ... PY` | 0 | Confirmed `dino_hsl2_mass_dse_wtg_mneutral` and `dino_hsl2_mass_dse_wtg` are registered and constructible through repository APIs. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_mneutral` | 0 | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.260258376022`. |
| `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_mneutral --workers 4` | 0 | `failed=False`, `issues=0`, `records=120`, `primary_score=-0.258933886891`. |
| `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_mneutral --workers 4` | skipped | Iteration primary delta did not meet the +0.002 promotion gate, so validation was not run. |
| `golden` | skipped | Forbidden for this scoring task. |

## Cache Reuse

Reused the cached incumbent iteration metrics from `outputs/eval/iteration_dino_hsl2_mass_dse_wtg.json` and `outputs/eval/iteration_dino_hsl2_mass_dse_wtg.csv`. The requested incumbent matches `.logbook/leaderboard.json`, the leaderboard fingerprint matches data path, target variables, lead range, and eval code commit `d8561caebb78ca096263d8c412217570ff2d1f46`, and the artifact is readable, finite, and has 60 incumbent model rows for the guardrails. No incumbent rerun was performed.

The cached validation incumbent metrics at `outputs/eval/validation_dino_hsl2_mass_dse_wtg.json` and `outputs/eval/validation_dino_hsl2_mass_dse_wtg.csv` were checked as valid but not used for a candidate comparison because validation was gated off.

Dirty paths during scoring were: `src/dynamaxx/dycore/models/dinosaur/__init__.py, src/dynamaxx/dycore/models/dinosaur/adapter.py, src/dynamaxx/dycore/registry.py, tests/dycore/models/dinosaur/test_dependency.py, tests/dycore/models/dinosaur/test_primitive_equations.py, tests/dycore/test_registry.py, gifs/`. These are candidate source/test paths plus the unrelated untracked `gifs/` directory and do not touch fixed evaluation code.

## Scores And Gates

| Protocol | Candidate primary | Incumbent primary | Delta | Gate |
| --- | ---: | ---: | ---: | --- |
| fast | -0.260258376022 | n/a | n/a | pass |
| iteration | -0.258933886891 | -0.258512354938 | -0.000421531953 | fail primary delta |
| validation | n/a | -0.257040331041 | n/a | skipped |

Iteration did not promote to validation because the primary delta `-0.000421531953` is below the required `+0.002`.

## Diagnostics And Guardrails

- Fast diagnostics: `failed=False`, `issues=0`.
- Iteration candidate diagnostics: `failed=False`, `issues=0`.
- Iteration incumbent diagnostics: `failed=False`, `issues=0`.
- Early lead mean RMSE guardrail: pass. Worst variable is `10m_u_component_of_wind` with relative change `0.000374411561` over leads 1-5 days.
- Single variable+lead RMSE guardrail: pass. Worst regression is `10m_u_component_of_wind` at lead `360` hours with relative change `0.001453065073` and absolute RMSE change `0.008196140585`.
- Best single-lead RMSE movement is `geopotential_500` at lead `24` hours with relative change `-0.000013112564`.

## Artifacts

- Candidate fast JSON: `outputs/eval/fast_dino_hsl2_mass_dse_wtg_mneutral.json`
- Candidate fast CSV: `outputs/eval/fast_dino_hsl2_mass_dse_wtg_mneutral.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_mneutral.json`
- Candidate iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_mneutral.csv`
- Cached incumbent iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg.json`
- Cached incumbent iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg.csv`
- Cached incumbent validation JSON checked but not used: `outputs/eval/validation_dino_hsl2_mass_dse_wtg.json`
- Cached incumbent validation CSV checked but not used: `outputs/eval/validation_dino_hsl2_mass_dse_wtg.csv`

## Measurement Lessons

- The pressure-thickness-neutral clipped WTG variant is numerically stable under fast and iteration, but it gives back `0.000421531953` primary score versus the incumbent, so its neutrality correction does not improve the fixed iteration objective.
- RMSE regressions are small and well under guardrails; the failure is broad primary-score degradation rather than an instability or a localized severe regression.
- Future WTG follow-ups should justify why mass-neutrality is expected to recover enough mean skill to clear `+0.002`, because this clipped neutral version mostly preserved fields while slightly worsening the aggregate score.

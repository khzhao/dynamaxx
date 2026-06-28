# Scoring Notes

## Inputs

- Proposal slug: `coupled-surface-residual-vector-decay`
- Candidate: `dino_hsl2_mass_dse_wtg_vdse_ramp_sfc_vec`
- Incumbent: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Worker count: 4
- Golden: not run

## Pre-Scoring Checks

The Orchestrator-provided pre-scoring records were used without rerunning tests:

- Full pytest: `uv run pytest`, exit 0, `261 passed, 2 skipped`.
- Focused pytest: `195 passed`.
- Candidate fast: `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_sfc_vec`, exit 0, primary `-0.2413961488632447`, diagnostics failed `false`, issue count `0`, 120 records.
- Registry check was repeated by the Scorer. Candidate and incumbent were both registered and creatable as `DinosaurPrimitiveEquationsDycoreModel`.
- `git diff --check` was accepted from the Orchestrator record and not rerun.

## Cache Reuse

The incumbent iteration cache was reused from `.logbook/leaderboard.json`:

- Leaderboard incumbent: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- Incumbent commit: `ff40def55ac707e8915c840b856a0aaa3345b046`
- Cached iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Cached iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`
- Cached iteration primary: `-0.2197104515448394`

The cache satisfied the Scorer reuse checks: requested incumbent matched the leaderboard incumbent, the artifact was readable, primary score was finite, diagnostics were clean, target variables and lead range matched, the fingerprint includes `iteration`, and current `HEAD` matched the leaderboard `eval_code_commit`. Dirty files were candidate model/test/registry files, not fixed evaluation protocol files. No incumbent rerun was performed.

Validation incumbent artifacts were present but not used because the candidate did not promote from iteration.

## Candidate Iteration

Command run:

```bash
uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_sfc_vec --workers 4
```

Exit status: 0

Raw outputs:

- `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp_sfc_vec.json`
- `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp_sfc_vec.csv`

Result:

- Candidate iteration primary: `-0.2368096372876574`
- Incumbent iteration primary: `-0.2197104515448394`
- Delta: `-0.01709918574281799`
- Candidate diagnostics failed: `false`
- Candidate diagnostic issue count: `0`

## Iteration Gate

The candidate does not promote to validation.

- Diagnostics gate: pass
- Primary delta gate: fail, because `-0.01709918574281799 < +0.002`
- Early day 1-5 mean RMSE guardrail: fail, because `2m_temperature` regressed by `2.904957387960501%`
- Per-variable and lead RMSE guardrail: pass, worst regression was `2m_temperature` at lead hour 216 with `3.9714099404882055%`, below the 10% threshold

Early day 1-5 mean RMSE guardrail by channel:

| Channel | Candidate mean RMSE | Incumbent mean RMSE | Relative regression |
| --- | ---: | ---: | ---: |
| `10m_u_component_of_wind` | 4.2914549976767375 | 4.291454635917505 | 0.000008429757810327926% |
| `2m_temperature` | 4.889359735984955 | 4.751335465357272 | 2.904957387960501% |
| `geopotential_500` | 592.5711687270714 | 592.5709106473444 | 0.00004355254744727127% |
| `mean_sea_level_pressure` | 771.1149491007974 | 771.1150019948005 | -0.0000068594182463573575% |

## Validation

Validation was skipped. The protocol allows validation only when iteration promotes, and this candidate failed the primary-score gate and the early day 1-5 mean RMSE guardrail.

No `validation` command was run for the candidate. Golden was not run.

## Anomalies And Lessons

- The iteration run was long and quiet between progress prints, but it continued making chunk progress and completed successfully.
- The evaluation records contain both evaluated-model rows and `persistence` rows. Guardrail comparisons were computed only from rows whose `model_name` matched the candidate or incumbent model.
- The surface residual vector decay changed the primary score materially in the wrong direction while leaving most non-temperature RMSE values nearly unchanged; future related proposals should specifically protect early-lead 2m-temperature behavior before spending validation compute.

# Scoring Notes: roughness-aware-surface-wind-diagnostic

## Inputs

- Candidate model: `dino_hsl2_mass_dse_wtg_vdse_z0_10m`
- Incumbent model: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- History directory: `.logbook/history/2026-06-26_04-36-24_roughness-aware-surface-wind-diagnostic`
- Worker count: 4
- Golden: not run
- Validation permission: allowed only if iteration promotes

## Pre-Scoring Records

- Full pytest was provided by the Orchestrator and was not rerun: `uv run pytest` exited 0 with `263 passed, 2 skipped in 455.51s`.
- Candidate fast was provided by the Orchestrator and verified from artifact: primary score `-0.22400258588040814`, diagnostics failed `False`, issue count `0`, records `120`.
- Candidate and incumbent registration were verified again by constructing both registered dycore models.

## Incumbent Cache Reuse

Iteration incumbent metrics were reused from the leaderboard cache:

- JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`
- Primary score: `-0.2197104515448394`
- Diagnostics failed: `False`
- Issue count: `0`

The cache is valid because the requested incumbent matches `.logbook/leaderboard.json`, the leaderboard fingerprint includes the `iteration` protocol, current `HEAD` matches the leaderboard `eval_code_commit` (`ff40def55ac707e8915c840b856a0aaa3345b046`), the artifacts are readable and finite, and the records needed for primary-score and RMSE guardrail comparisons are present. Candidate source edits do not invalidate the accepted incumbent cache under `roles/SCORER.md`.

Validation incumbent metrics were also checked as available from the leaderboard cache, but candidate validation was skipped because iteration did not promote.

## Candidate Iteration

Command run:

```bash
uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_z0_10m --workers 4
```

Result:

- Exit status: 0
- JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_z0_10m.json`
- CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_z0_10m.csv`
- Primary score: `-0.21994736458089423`
- Incumbent primary score: `-0.2197104515448394`
- Primary delta: `-0.00023691303605483105`
- Diagnostics failed: `False`
- Issue count: `0`
- Metric records: `120`

## Iteration Gate

Promotion threshold requires candidate primary score at least `+0.002` above incumbent and clean guardrails.

- Diagnostics pass: `True`
- Primary delta pass: `False` (`-0.00023691303605483105` vs `+0.002`)
- Early day 1-5 mean RMSE guardrail pass: `True`
- Worst variable+lead RMSE guardrail pass: `True`
- Promotes to validation: `False`

Early day 1-5 mean RMSE guardrail by channel:

| Channel | Candidate mean RMSE | Incumbent mean RMSE | Relative regression | Pass |
|---|---:|---:|---:|---|
| 10 m zonal wind | 4.29446825880518 | 4.291454635917505 | 0.0007022380855321846 | True |
| 2 m temperature | 4.751335466717757 | 4.751335465357272 | 2.863374030024968e-10 | True |
| 500 hPa geopotential | 592.5709934659734 | 592.5709106473444 | 1.3976155013864038e-07 | True |
| Mean sea level pressure | 771.1150517670918 | 771.1150019948005 | 6.454587337574659e-08 | True |

Worst variable+lead RMSE regression:

- Variable: `10 m zonal wind`
- Lead hours: `264`
- Candidate RMSE: `5.485980425994694`
- Incumbent RMSE: `5.47932500473572`
- Relative regression: `0.001214642543237071`
- Passes 10% guardrail: `True`

## Validation Status

Validation was skipped. The candidate iteration primary delta was `-0.00023691303605483105`, below the required `+0.002` promotion threshold, so protocol does not allow candidate validation for this implementation state.

## Anomalies And Lessons

- Initial text inspection with `rg` produced terminal-truncated output due large JSON files; all reported values come from structured JSON parsing.
- Candidate iteration ran for a long supervised interval and completed successfully; no evaluator failure or diagnostic issue was reported.
- The roughness-aware wind diagnostic was slightly worse than the cached incumbent on iteration primary score. The worst RMSE regression was small (`0.001214642543237071`), but the candidate did not produce the needed aggregate gain.
- No incumbent metrics were recomputed, and no golden evaluation was run.

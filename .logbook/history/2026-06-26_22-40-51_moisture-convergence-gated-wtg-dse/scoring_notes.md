# Scoring Notes

## Inputs

- Candidate: `dino_hsl2_mass_dse_wtg_vdse_mfcgate`
- Incumbent: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- History directory: `.logbook/history/2026-06-26_22-40-51_moisture-convergence-gated-wtg-dse`
- Worker count: `4`
- Validation permission: validation allowed only after iteration promotion; iteration did not promote, so validation was skipped.
- Golden: not run.

## Gate Status

- Fast gate: passed from supplied artifact, primary `-0.22390463383670187`, diagnostics failed `false`, issue count `0`.
- Iteration promotion gate: failed. Candidate primary `-0.21974636083207516`, cached incumbent primary `-0.2197104515448394`, delta `-3.590928723576359e-05`, required delta `+0.002`.
- Validation acceptance gate: skipped because the iteration promotion gate failed; no validation command was run.

## Cache Reuse

The incumbent leaderboard cache was reused for iteration. No incumbent rerun was performed.

Validation checks performed:

- Requested incumbent matched .logbook/leaderboard.json.incumbent_model_name.
- Leaderboard fingerprint included iteration and matched the fixed data path, target variables, and lead range.
- Current HEAD matched .logbook/leaderboard.json.evaluation_fingerprint.eval_code_commit.
- Dirty worktree entries were candidate source/test edits; candidate edits do not invalidate the accepted incumbent cache.
- Cached incumbent iteration JSON/CSV existed, were readable, contained a finite primary_score, clean diagnostics, and complete 4-variable x 15-lead records.

Reused artifacts:

- Iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`

Cached validation artifacts were not used for a candidate comparison because validation was skipped:

- Validation JSON pointer: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Validation CSV pointer: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`

## Commands

- `uv run pytest`: exit 0, supplied by Orchestrator, `260 passed, 2 skipped in 305.04s`; Scorer did not rerun.
- `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_mfcgate`: exit 0, supplied by Orchestrator; Scorer parsed the artifact.
- `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_mfcgate --workers 4`: exit 0, completed at `2026-06-27T01:35:07Z` from metrics mtime.
- `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_mfcgate --workers 4`: not run; iteration did not promote.

## Iteration Guardrails

- Candidate diagnostics failed: `false`
- Candidate diagnostic issue count: `0`
- Incumbent diagnostics failed: `false`
- Incumbent diagnostic issue count: `0`

Early day 1-5 mean RMSE guardrail:

| Channel | Candidate | Incumbent | Relative regression |
| --- | ---: | ---: | ---: |
| `10m_u_component_of_wind` | 4.778312127969069 | 4.778312125062429 | 6.082983483621549e-10 |
| `2m_temperature` | 2.7938222588714074 | 2.7938222602375182 | -4.889755513431627e-10 |
| `geopotential_500` | 878.0844086079817 | 878.0844086667236 | -6.689775468524088e-11 |
| `mean_sea_level_pressure` | 817.7806709709877 | 817.7806714218246 | -5.512932674629605e-10 |

Worst variable+lead RMSE regression:

- Channel: `10m_u_component_of_wind`
- Lead hours: `144`
- Candidate RMSE: `5.260300308617497`
- Incumbent RMSE: `5.260300291937419`
- Relative regression: `3.170936417645094e-09`

RMSE guardrails were clean: max early day 1-5 mean RMSE regression was 
`6.082983483621549e-10` against threshold `0.02`, and worst variable+lead RMSE regression was `3.170936417645094e-09` against threshold `0.1`.

## Measurement Lessons

- The moisture-convergence gate did not improve the accepted ramp incumbent on iteration primary score; the delta was slightly negative despite clean diagnostics and RMSE guardrails.
- The RMSE guardrail changes are near numerical noise, so the useful signal is the aggregate primary-score regression rather than an obvious isolated variable/lead failure.
- The incumbent cache policy worked as intended: candidate source edits did not force an incumbent rerun because the cached accepted artifacts remained compatible and complete.

## Anomalies

- Cache reuse: incumbent iteration metrics reused from `.logbook/leaderboard.json`; no cache invalidation found.
- Resource limits: none observed in the completed candidate iteration run.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none observed; diagnostics were clean and primary scores were finite.

## Recommendation To Orchestrator

Report the measured gate status and caveats. The Scorer does not accept or reject the candidate.

# Scoring Notes

## Inputs

- Candidate: `dino_hsl2_mass_dse_wtg_vdse_ramp_precenter_wtg`
- Incumbent: `dino_hsl2_mass_dse_wtg_vdse_ramp`
- History directory:
  `.logbook/history/2026-06-27_01-53-10_recenter-before-wtg-filter-order`
- Worker count: `4`
- Validation permission: validation allowed only after iteration promotion;
  iteration did not promote, so validation was skipped.
- Golden: not run.

## Gate Status

- Fast gate: passed, primary `-0.2238125004828227`, diagnostics failed
  `false`, issue count `0`.
- Iteration promotion gate: failed. Candidate primary
  `-0.21971074781018693`, cached incumbent primary `-0.2197104515448394`,
  delta `-2.9626534753246503e-07`, required delta `+0.002`.
- Validation acceptance gate: skipped because the iteration promotion gate
  failed; no validation command was run.

## Cache Reuse

The incumbent leaderboard cache was reused for iteration. No incumbent rerun
was performed.

Validation checks performed:

- Requested incumbent matched `.logbook/leaderboard.json.incumbent_model_name`.
- Leaderboard fingerprint included iteration and matched the fixed data path,
  target variables, and lead range.
- Current HEAD matched
  `.logbook/leaderboard.json.evaluation_fingerprint.eval_code_commit` before
  candidate edits.
- Dirty worktree entries were candidate source/test edits; candidate edits do
  not invalidate the accepted incumbent cache.
- Cached incumbent iteration JSON/CSV existed, were readable, contained a
  finite primary score, clean diagnostics, and complete 4-variable x 15-lead
  records.

Reused artifacts:

- Iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`

Cached validation artifacts were not needed because validation was skipped:

- Validation JSON pointer:
  `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Validation CSV pointer:
  `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`

## Commands

- `uv run pytest`: exit 0, `258 passed, 2 skipped in 347.65s`.
- `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_precenter_wtg`:
  exit 0, failed `false`, issues `0`, records `120`.
- `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_precenter_wtg --workers 4`:
  exit 0, failed `false`, issues `0`, records `120`.
- `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_ramp_precenter_wtg --workers 4`:
  not run; iteration did not promote.

## Iteration Guardrails

- Candidate diagnostics failed: `false`
- Candidate diagnostic issue count: `0`
- Incumbent diagnostics failed: `false`
- Incumbent diagnostic issue count: `0`

Early day 1-5 mean RMSE guardrail:

| Channel | Candidate | Incumbent | Relative regression |
| --- | ---: | ---: | ---: |
| `10m_u_component_of_wind` | 4.291455792308885 | 4.291454635917505 | 2.694637315533217e-07 |
| `2m_temperature` | 4.751334843788252 | 4.751335465357272 | -1.3081985576176294e-07 |
| `geopotential_500` | 592.5718086880131 | 592.5709106473444 | 1.5154990780144199e-06 |
| `mean_sea_level_pressure` | 771.1152088202696 | 771.1150019948005 | 2.682161136804278e-07 |

Worst variable+lead RMSE regression:

- Channel: `geopotential_500`
- Lead hours: `24`
- Candidate RMSE: `245.96255548882735`
- Incumbent RMSE: `245.96134960647697`
- Relative regression: `4.902731068543002e-06`

RMSE guardrails were clean: max early day 1-5 mean RMSE regression was
`1.5154990780144199e-06` against threshold `0.02`, and worst variable+lead RMSE
regression was `4.902731068543002e-06` against threshold `0.1`.

## Measurement Lessons

- Reordering theta recentering before tropical WTG is numerically stable but
  effectively neutral and slightly negative against the accepted incumbent.
- The two rollout-only filters nearly commute under the current step size,
  masks, and caps; there is no evidence that final theta recentering is diluting
  a useful WTG signal enough to affect the fixed primary score.
- The incumbent cache policy worked as intended: candidate source edits did not
  force an incumbent rerun because the accepted incumbent artifacts remained
  compatible and complete.

## Anomalies

- Cache reuse: incumbent iteration metrics reused from `.logbook/leaderboard.json`;
  no cache invalidation found.
- Resource limits: none observed.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none observed; diagnostics were clean and
  primary scores were finite.

## Recommendation To Orchestrator

Report the measured gate status and caveats. The Scorer does not accept or
reject the candidate.

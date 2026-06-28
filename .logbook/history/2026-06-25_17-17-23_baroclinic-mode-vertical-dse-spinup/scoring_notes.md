# Scoring Notes

## Gate Status

- Fast gate: passed from verified pre-scoring artifact `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_bm.json`; diagnostics failed=false, issues=0, primary=-0.23079739639076055.
- Iteration promotion gate: failed. Candidate primary=-0.22588531808146894; cached incumbent primary=-0.2197104515448394; delta=-0.0061748665366295474, below the +0.002 threshold. Candidate iteration diagnostics failed=false, issues=0.
- Iteration guardrails: early day 1-5 mean RMSE guardrail failed for `2m_temperature` at relative regression 0.026769825875213316 (> 0.02). Worst variable+lead RMSE guardrail passed; worst was `2m_temperature` at lead_hours=48 with relative regression 0.046056873668183194 (<= 0.10).
- Validation acceptance gate: not run because iteration did not promote. Cached incumbent validation primary for reporting is -0.21940899263836755.

## Commands And Status

- Provided, not rerun: `uv run pytest` -> exit 0 per Orchestrator record (`258 passed, 2 skipped in 277.83s`).
- Provided, not rerun: `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_bm` -> exit 0 per Orchestrator record; artifact verified clean and finite.
- Ran: `uv run python - <<'PY'` registry construction check -> exit 0; both `dino_hsl2_mass_dse_wtg_vdse_bm` and `dino_hsl2_mass_dse_wtg_vdse_ramp` construct from `dynamaxx.dycore.registry`.
- Ran: `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_bm --workers 4` -> exit 0; wrote `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_bm.json` and `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_bm.csv`.
- Ran: first scratch guardrail parser -> exit 1 because it incorrectly assumed one record per channel/lead; repository records include a persistence baseline row per channel/lead. No artifacts were changed by this failed parser.
- Ran: corrected guardrail parser filtering rows where `model_name` equals the candidate or incumbent -> exit 0.
- Not run: `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_bm --workers 4`, because iteration did not promote.
- Not run: golden protocol, as instructed.

## Cache Reuse

- Iteration incumbent cache reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json` and `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`.
- Validation incumbent cache reused for reporting from `.logbook/leaderboard.json`: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json` and `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`.
- Cache checks passed: requested incumbent matched leaderboard incumbent; leaderboard fingerprint covers iteration and validation; `git rev-parse HEAD` matched leaderboard `eval_code_commit` (`ff40def55ac707e8915c840b856a0aaa3345b046`); evaluation source files were not dirty; cached artifacts were readable, finite, clean, and contained matching target variable/lead records.
- Candidate source edits in the dirty worktree were not treated as cache invalidation, per protocol.

## Guardrail Details

Early day 1-5 mean RMSE regressions:
- `2m_temperature`: candidate_mean=4.8785278884396117, incumbent_mean=4.7513354653572719, relative_regression=0.026769825875213316, passed=false
- `10m_u_component_of_wind`: candidate_mean=4.3141412471169138, incumbent_mean=4.2914546359175052, relative_regression=0.005286461846650342, passed=true
- `mean_sea_level_pressure`: candidate_mean=775.18604631673554, incumbent_mean=771.11500199480054, relative_regression=0.0052794256516908687, passed=true
- `geopotential_500`: candidate_mean=593.6920294156082, incumbent_mean=592.57091064734436, relative_regression=0.0018919571449079289, passed=true

Worst variable+lead RMSE regressions:
- `2m_temperature` lead_hours=48: candidate=4.1711684440444046, incumbent=3.9875159267559379, relative_regression=0.046056873668183194, passed=true
- `2m_temperature` lead_hours=72: candidate=5.2602922298938957, incumbent=5.0456241503010713, relative_regression=0.042545396406511019, passed=true
- `2m_temperature` lead_hours=96: candidate=5.9437138197048291, incumbent=5.8045115946116193, relative_regression=0.023981729181561561, passed=true
- `2m_temperature` lead_hours=120: candidate=6.4093495048071984, incumbent=6.3246124204450052, relative_regression=0.013397988481993197, passed=true
- `10m_u_component_of_wind` lead_hours=72: candidate=4.5172247631325417, incumbent=4.4771924820240745, relative_regression=0.008941380400596317, passed=true
- `2m_temperature` lead_hours=144: candidate=6.7646474547378981, incumbent=6.7124191677089913, relative_regression=0.0077808440927166931, passed=true
- `10m_u_component_of_wind` lead_hours=96: candidate=4.9516353630571075, incumbent=4.9141683703476025, relative_regression=0.0076242794071898733, passed=true
- `mean_sea_level_pressure` lead_hours=72: candidate=834.099865629634, incumbent=828.26326061722693, relative_regression=0.0070467993570758987, passed=true
- `mean_sea_level_pressure` lead_hours=96: candidate=966.32969271744014, incumbent=959.70135161027304, relative_regression=0.0069066705971034398, passed=true
- `mean_sea_level_pressure` lead_hours=120: candidate=1064.5636049975749, incumbent=1058.29378880737, relative_regression=0.005924457137058867, passed=true

## Measurement Lessons

- The baroclinic-mode vertical-DSE spinup candidate was worse than the pressure-ramped incumbent on iteration primary score despite clean diagnostics.
- The main guardrail regression was early `2m_temperature`; future related proposals should check whether internal-mode spinup is adding near-surface thermal error during days 1-5.
- Evaluation JSON includes persistence baseline records in addition to model records, so scorer guardrail scripts must filter by `model_name` before model-to-model RMSE comparisons.

## Anomalies

- Cache reuse: no incumbent rerun; cache was valid and authoritative.
- Resource limits: no resource failures reported by the evaluator. Candidate iteration used `--workers 4` with GPU device dispatch.
- Failed or restarted commands: one scratch parser command failed with the duplicate-row assumption described above; fixed parser succeeded. The fixed evaluation command itself exited 0.
- Nonfinite or unstable outputs: none detected in fast, candidate iteration, or reused incumbent artifacts.

## Recommendation To Orchestrator

Report the measured gate status: iteration did not promote to validation. This Scorer measurement does not accept or reject the candidate.

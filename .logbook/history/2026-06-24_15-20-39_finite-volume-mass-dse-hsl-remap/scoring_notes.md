# Scoring Notes

## Gate Status

- Fast gate: passed using the existing authorized candidate fast artifact. Candidate fast primary_score=`-0.2639376282387718`, failed=`False`, issue_count=`0`.
- Iteration promotion gate: failed. Candidate iteration primary_score=`-0.26214561232546824`; cached incumbent iteration primary_score=`-0.2616483974683927`; signed delta=`-0.0004972148570755452`, below the `+0.002` promotion threshold.
- Iteration diagnostics: passed. Candidate iteration failed=`False`, issue_count=`0`.
- Iteration early day 1-5 mean RMSE guard: passed. Worst relative regression was `0.000613520041624484` (0.061352004162448404%) for `2m_temperature`, below the `+2%` threshold.
- Iteration variable+lead RMSE guard: passed. Worst positive regression was `0.0009484825576416079` (0.09484825576416078%) for `2m_temperature` at `312` h, below the `+10%` threshold. Variable+lead regressions above `+10%`: `0`.
- Validation acceptance gate: not run because iteration did not promote. Golden was not run.

## Commands And Status

- Reused Orchestrator full pytest record, not rerun by Scorer: `uv run pytest` exit `0`, `244 passed`, `2 skipped` in `195.21s`.
- Reused Implementer focused checks, not rerun by Scorer: scoped `ruff check` passed; `pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k "finite_volume or fv_remap or mass_dse"` passed with `9 passed`; `pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` passed with `47 passed`.
- Scorer registration/cache/fast verification: `uv run python - <<'PY' ... confirm model registration, validate incumbent caches, validate candidate fast artifact ... PY` exit `0`.
- Reused candidate fast command/artifact: `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_fv_remap` exit `0` from the Implementer handoff, primary_score=`-0.2639376282387718`.
- Scorer iteration command: `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_fv_remap --workers 4` exit `0`; console reported `chunks=229`, `cached=0`, `pending=229`, `effective_workers=4`; result primary_score=`-0.26214561232546824`.
- Scorer guardrail computation: `uv run python - <<'PY' ... compute exact iteration delta and fixed RMSE guardrails ... PY` exit `0`.
- Candidate validation command: `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_fv_remap --workers 4` was not run because iteration promotion failed.

## Cache Reuse

- Iteration incumbent cache: reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dino_hsl2_mass_dse.json` and `outputs/eval/iteration_dino_hsl2_mass_dse.csv`.
- Validation incumbent cache: checked and compatible, but not used for a candidate comparison because validation was skipped: `outputs/eval/validation_dino_hsl2_mass_dse.json` and `outputs/eval/validation_dino_hsl2_mass_dse.csv`.
- Cache validation checks: requested incumbent matched the leaderboard; fingerprint data path, protocols, target variables, lead range, and eval code commit matched; artifacts were readable; primary scores were finite; diagnostics were clean; records covered incumbent rows for all target channels and 24..360 h leads.
- Candidate source edits in the current worktree were not treated as incumbent cache invalidation, per protocol.

## Guardrail Details

- Early day 1-5 mean RMSE relative deltas:
- `10m_u_component_of_wind`: candidate `4.372212650919975`, incumbent `4.371016832235197`, relative delta `0.0002735790619608074` (0.02735790619608074%).
- `2m_temperature`: candidate `4.723063314432228`, incumbent `4.720167397134263`, relative delta `0.000613520041624484` (0.061352004162448404%).
- `geopotential_500`: candidate `603.0629420501616`, incumbent `603.1650920588065`, relative delta `-0.00016935663218877565` (-0.016935663218877565%).
- `mean_sea_level_pressure`: candidate `782.7260843157129`, incumbent `782.5186026540035`, relative delta `0.0002651459799239045` (0.02651459799239045%).
- Worst variable+lead RMSE regression: `2m_temperature`, lead `312` h, candidate RMSE `7.717868353760516`, incumbent RMSE `7.710555026807853`, relative delta `0.0009484825576416079` (0.09484825576416078%).

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dino_hsl2_mass_dse_fv_remap.json`
- Candidate fast CSV: `outputs/eval/fast_dino_hsl2_mass_dse_fv_remap.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_fv_remap.json`
- Candidate iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_fv_remap.csv`
- Candidate validation JSON/CSV: not produced because validation was skipped.
- Cached incumbent iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse.json`
- Cached incumbent iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse.csv`
- Cached incumbent validation JSON: `outputs/eval/validation_dino_hsl2_mass_dse.json`
- Cached incumbent validation CSV: `outputs/eval/validation_dino_hsl2_mass_dse.csv`
- Candidate iteration run directory: `outputs/eval/runs/iteration_dino_hsl2_mass_dse_fv_remap`
- Score artifacts written here: `.logbook/history/2026-06-24_15-20-39_finite-volume-mass-dse-hsl-remap/scores.json` and `.logbook/history/2026-06-24_15-20-39_finite-volume-mass-dse-hsl-remap/scoring_notes.md`

## Measurement Lessons

- The finite-volume-style mass-DSE remap was numerically stable on fast and iteration, but it reduced the fixed iteration primary score by `-0.0004972148570755452` versus the accepted incumbent.
- The primary-score miss is not explained by fixed RMSE guardrail failures: early day 1-5 mean RMSE regressions were below `2%`, and the worst variable+lead RMSE regression was below `10%`.
- The candidate was much slower than typical Dinosaur-family iteration runs. It completed without restart, but future remap proposals should account for the extra runtime cost before promotion scoring.

## Anomalies

- Cache reuse: no anomaly; incumbent iteration artifacts were valid and reused. Incumbent validation artifacts were valid but not used because validation was skipped.
- Resource limits: no resource failure observed. The run used 4 effective GPU workers.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by diagnostics.
- Runtime: candidate iteration took about `2h51m50s` from run manifest creation to final metrics write; this was slow but not treated as hung because chunk progress and GPU utilization were steady.

## Recommendation To Orchestrator

Report measured gate status only. The candidate failed iteration promotion on primary-score delta and validation was skipped. The Scorer does not accept or reject the candidate.

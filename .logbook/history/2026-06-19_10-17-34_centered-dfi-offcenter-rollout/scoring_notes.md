# Scoring Notes

## Gate Status

- Fast gate: passed using the verified Implementer artifact. Candidate fast primary_score=-0.557898834008192, failed=False, issues=0, records=120.
- Registration gate: passed. Candidate and incumbent are registered and instantiate with exact names; the incumbent has `use_centered_dfi_solver_with_offcentered_rollout=False`, while the candidate has it `True`.
- Iteration promotion gate: failed by primary-delta threshold. Candidate primary_score=-0.5719815909858376; incumbent primary_score=-0.5719873627530224; iteration_delta=+0.000005771767185, below the +0.002 threshold. Candidate diagnostics were clean: failed=False, issues=0.
- Iteration early day 1-5 mean RMSE guard: passed. No target variable exceeded the +2.0% threshold. By variable: 10m_u_component_of_wind +0.002344%, 2m_temperature +0.000851%, geopotential_500 +0.002002%, mean_sea_level_pressure +0.000253%.
- Iteration variable+lead RMSE guard: passed. No variable+lead exceeded the +10.0% threshold; the largest positive change was geopotential_500 day 1.0 at +0.009600%.
- Validation acceptance gate: not run. Protocol allows validation only after iteration passes; this candidate did not reach the +0.002 iteration primary-delta threshold.
- Golden: not run, as required.

## Measurement Lessons

- Centered DFI with offcentered rollout was numerically clean but did not materially change the fixed iteration score: the observed gain was only +0.000005771767184858945.
- RMSE changes were near-zero across the guardrails. The largest early mean RMSE regression was only +0.002344% for `10m_u_component_of_wind`, and the largest variable+lead regression was +0.009600% for `geopotential_500` at day 1.
- Future proposals in this area should target a stronger mechanism than the DFI solver selector alone, since this change did not clear the promotion threshold despite clean diagnostics.

## Anomalies

- Cache reuse: candidate focused pytest, selected dycore tests, full pytest, `git diff --check`, and fast records were reused from the Implementer verification as authorized. Candidate iteration was freshly run with `cached=0`, `pending=229` at startup.
- Incumbent cache reuse: incumbent iteration was reused from `.logbook/leaderboard.json` at `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter.json`. Cache checks passed under the task-specific side-by-side guidance: incumbent model and eval commit matched the leaderboard, the raw JSON was readable with finite primary score, `src/dynamaxx/eval` and `time_integration.py` had no uncommitted changes, and the incumbent factory still constructs with the new centered-DFI flag false.
- Validation cache reuse: not applicable because validation was not run or scored.
- Resource limits: none observed. Candidate iteration used 4 effective GPU workers over 229 chunks and completed with exit status 0.
- Failed or restarted commands: one preliminary read-only registry probe attempted to import nonexistent `get_model` and exited 1; the corrected `create_dycore_model()` registration check passed. No evaluation command used for scoring failed or restarted.
- Nonfinite or unstable outputs: none reported. Candidate fast and candidate/incumbent iteration diagnostics had `failed=False` and zero issues.

## Recommendation To Orchestrator

Report measured gate status only: fast passed, iteration did not promote to validation because the primary delta was below threshold, validation and golden were not run. The Scorer does not accept or reject the candidate.

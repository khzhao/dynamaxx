# Scoring Notes

## Gate Status

- Fast gate: passed. Reused `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_qpos.json`; exact-filtered candidate records `60`, persistence records `60`, diagnostics `failed=false`, issues `0`, primary `-1.1909729416286097`.
- Iteration promotion gate: failed on primary score. Candidate `-1.2218428097613614` versus incumbent `-1.2218408656785489`, delta `-0.0000019440828125105725`; required delta is `+0.002`.
- Iteration diagnostics: clean. Candidate diagnostics `failed=false`, issues `0`; incumbent diagnostics `failed=false`, issues `0`.
- RMSE guardrails: passed. Worst early day 1-5 mean RMSE regression was `5.736504032213701e-8` for `mean_sea_level_pressure`; worst variable-lead RMSE regression was `1.592198976555658e-5` for `geopotential_500` at lead hour `168`.
- Validation acceptance gate: not run. Protocol only allows validation after the iteration promotion gate passes.

## Measurement Lessons

- The diagnostic-time passive humidity floor produced only numerical-scale movement relative to the incumbent. It slightly improved early `geopotential_500` mean RMSE but worsened longer-lead `geopotential_500` by at most `0.001592%`, leaving the aggregate primary score effectively unchanged and below the promotion threshold.
- Future humidity proposals should include evidence that humidity diagnostic undershoots materially affect evaluated variables before spending a full iteration run. The current result suggests passive humidity positivity is not a meaningful remaining error source for this incumbent.

## Anomalies

- Cache reuse: reused compatible incumbent iteration and validation artifacts from the leaderboard. Candidate iteration reported `cached=0` and ran all `229` chunks.
- Resource limits: no resource pressure observed. Snapshot before scoring: `48` CPUs, about `174Gi` available RAM, four NVIDIA L4 GPUs with about `22566 MiB` free each, and `4.1T` free disk. Worker count was `4`.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none. Candidate fast and iteration diagnostics were clean.

## Command Record

- Registration check: `uv run python - <<'PY' ... create_dycore_model(...) ... PY`, exit `0`.
- Fast verification: `python -m json.tool outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_qpos.json`, exit `0`.
- Candidate iteration: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_qpos --workers 4`, exit `0`, started `2026-06-16T21:21:44Z`, finished `2026-06-16T22:07:24Z`.
- Validation: not run because the iteration promotion gate failed.
- Golden: not run.

## Recommendation To Orchestrator

Report the measured gate status and caveats. The Scorer does not accept or reject the candidate.

# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_mass_dse_vdse` exited 0 with `failed=False`, `issues=0`, and primary score `-0.2017801581629101`.
- Iteration promotion gate: failed. Candidate iteration score was `-0.206563907329551` versus cached incumbent `-0.2616483974683927`, so the primary delta was `+0.0550844901388417` and passed the `+0.002` threshold. Diagnostics were clean, and day-1-to-5 mean RMSE guardrails passed; the largest early mean regression was `2m_temperature` at `+1.0189086270942393%` against the `2%` limit. The single variable/lead guardrail failed: `mean_sea_level_pressure` at `24h` regressed from RMSE `380.0773181846907` to `426.628518862156`, a `+12.24782391640764%` regression against the `10%` limit.
- Validation acceptance gate: not evaluated. Validation permission was contingent on iteration promotion, and the candidate did not promote. Golden was not run.

## Measurement Lessons

- The vertical DSE transport candidate substantially improved iteration primary score, driven by later-lead or aggregate skill, but introduced an unacceptable day-1 mean sea level pressure RMSE regression.
- Future variants of this mechanism should specifically protect short-lead pressure adjustment before relying on the strong primary-score movement.

## Anomalies

- Cache reuse: reused `.logbook/leaderboard.json` incumbent artifacts for iteration and checked validation cache for reporting. The requested incumbent matched `dino_hsl2_mass_dse`; `HEAD` matched the leaderboard `eval_code_commit` `2c70bb5b77370a074330c2b46954f74f20771f12`; the fingerprint matched the requested data path, target variables, lead range, and protocols; artifacts were present, readable, finite, and contained required model rows. Candidate source edits in the current worktree were not treated as cache invalidation.
- Resource limits: no resource failures were observed. Iteration ran with `--workers 4`; evaluator reported GPU dispatch with `gpu_count=4`, `effective_workers=4`. The run had a long quiet startup, but a separate resource check showed all four GPUs at 100% utilization and four active worker processes.
- Failed or restarted commands: no scoring command failed or was restarted.
- Nonfinite or unstable outputs: no nonfinite primary scores or diagnostic issues were observed in fast or iteration.

## Recommendation To Orchestrator

Report measured status as iteration-not-promoted. Do not run validation for this candidate under the stated gate because the worst variable+lead RMSE regression exceeded the `10%` guardrail, despite clean diagnostics and a strongly positive iteration primary-score delta.

# Scoring Notes

## Gate Status

- Fast gate: passed from the Implementer-provided artifact after exact model-name filtering. Candidate fast primary was `-1.1911638361399597`, diagnostics had `failed=false`, issue count was `0`, and the artifact contained `60` candidate rows plus `60` persistence rows.
- Iteration promotion gate: did not promote. Candidate primary was `-1.2220957940878374`; incumbent primary was `-1.2218408656785489`; delta was `-0.0002549284092885351`, below the required `+0.002`.
- Iteration guardrails: clean. Candidate and incumbent diagnostics were clean, early day 1-5 mean RMSE regressions were all below `2%`, and the worst variable-lead RMSE regression was `0.0005529361348106701` for `geopotential_500` at 72 hours, below the `10%` cap.
- Validation acceptance gate: skipped by protocol because the iteration primary threshold failed. Golden was not run.

## Command Record

- Provided by Implementer, not rerun by Scorer: `python -m compileall -q ...` exit `0`; `uv run ruff format ...` exit `0`; `uv run ruff check ...` exit `0`; focused pytest exit `0`, `44 passed`; full `uv run pytest` exit `0`, `110 passed, 2 skipped`; fast eval exit `0`; `git diff --check` exit `0`.
- Scorer registration check: first probe used the non-existent `get_model` helper and exited `1`; corrected repository-API check with `create_dycore_model` and `dycore_model_names` exited `0` for both candidate and incumbent.
- Resource checks: `48` CPUs, `174 GiB` available RAM, `4.1 TiB` free disk, and four NVIDIA L4 GPUs with about `22566 MiB` free each before the run.
- Iteration command: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_600s --workers 4`, started `2026-06-16T18:49:10Z`, finished `2026-06-16T19:48:52Z`, exit `0`.
- Validation command: not run because iteration did not promote.

## Measurement Lessons

- Exact model-name filtering is required because fast and iteration JSON files include persistence rows alongside model rows.
- The fixed `600 s` inner step was numerically stable but slightly degraded the aggregate iteration primary score versus the `900 s` incumbent.
- The RMSE guardrails were not the limiting factor; the largest relative variable-lead regression was only about `0.0553%`.

## Anomalies

- Cache reuse: candidate fast was reused from the Implementer artifact; candidate iteration was a fresh run with `229` chunks and `0` cached chunks.
- Resource limits: none observed. The run used 4 GPU workers and completed without memory or disk pressure.
- Failed or restarted commands: one harmless registration preflight failed because Scorer attempted to import a non-existent `get_model` helper before checking `registry.py`; the corrected repository API check passed. No evaluation command failed or restarted.
- Nonfinite or unstable outputs: none reported by fast or iteration diagnostics.

## Recommendation To Orchestrator

Report the measured gate status and caveats. The Scorer does not accept or reject the candidate, but validation is not permitted because the iteration promotion gate failed.

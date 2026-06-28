# Scoring Notes

## Gate Status

- Fast gate: passed from the Implementer-provided artifact after exact model-name filtering. Candidate fast primary was `-1.1910009401848078`, diagnostics had `failed=false`, issue count was `0`, and the artifact contained `60` candidate rows plus `60` persistence rows.
- Iteration promotion gate: did not promote. Candidate primary was `-1.2220454761111341`; incumbent primary was `-1.2218408656785489`; delta was `-0.00020461043258523937`, below the required `+0.002`.
- Iteration guardrails: clean. Candidate and incumbent diagnostics were clean, early day 1-5 mean RMSE regressions were all below `2%`, and the worst variable-lead RMSE regression was `0.00038858055968793437` for `2m_temperature` at 336 hours, below the `10%` cap.
- Validation acceptance gate: skipped by protocol because the iteration primary threshold failed. Golden was not run.

## Command Record

- Provided by Implementer, not rerun by Scorer: `python -m compileall -q ...` exit `0`; `uv run ruff format ...` exit `0`; `uv run ruff check ...` exit `0`; focused pytest exit `0`, `43 passed`; full `uv run pytest` exit `0`, `109 passed, 2 skipped`; fast eval exit `0`; `git diff --check` exit `0`.
- Scorer registration check: `create_dycore_model` and `dycore_model_names` exited `0` for both `dinosaur_dfi_surface_residual_weak_hs_div_damp` and `dinosaur_dfi_surface_residual_weak_hs`.
- Resource checks: `48` CPUs, `174 GiB` available RAM after the run, `4.1 TiB` free disk, and four NVIDIA L4 GPUs with `22566 MiB` free each after the run.
- Iteration command: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_div_damp --workers 4`, exit `0`; fresh run with `229` chunks, `0` cached chunks, and 4 GPU workers.
- Validation command: not run because iteration did not promote.

## Measurement Lessons

- Exact model-name filtering is required because fast and iteration JSON files include persistence rows alongside model rows.
- Divergence-selective damping was numerically stable and guardrail-clean, but it slightly degraded the aggregate iteration primary score versus the weak-Held-Suarez incumbent.
- The limiting factor was primary score movement, not RMSE guardrails: the worst variable-lead RMSE regression was only about `0.0389%`.

## Anomalies

- Cache reuse: candidate fast was reused from the Implementer artifact; candidate iteration was a fresh run with `229` chunks and `0` cached chunks.
- Resource limits: none observed. The run used 4 GPU workers and completed without memory or disk pressure.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by fast or iteration diagnostics.

## Recommendation To Orchestrator

Report the measured gate status and caveats. The Scorer does not accept or reject the candidate, but validation is not permitted because the iteration promotion gate failed.

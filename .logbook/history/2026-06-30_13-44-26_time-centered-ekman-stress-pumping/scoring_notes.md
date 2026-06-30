# Scoring Notes: time-centered-ekman-stress-pumping

## Gate Status

- Candidate: `dino_ri2m_ekman_tcenter`
- Incumbent: `dino_ri2m_ekman_coupled`
- Fast artifact was verified instead of rerun: primary `-0.16795463351583548`, failed `False`, issues `0`.
- Candidate iteration completed with primary `-0.1652580985873155`, failed `False`, issues `0`.
- Cached incumbent iteration primary: `-0.16500618979404214`.
- Iteration primary delta: `-0.0002519087932733588`. Required for validation: `+0.002`.
- Iteration guardrails were clean after filtering to evaluated-model rows only: no early-lead mean RMSE regression above 2% and no single variable-lead RMSE regression above 10%.
- Iteration gate did not pass because the primary delta was below the validation threshold.
- Validation was skipped. Golden was not run.

## Cache Validation

- Incumbent was reused from `.logbook/leaderboard.json`; no incumbent iteration or validation command was run.
- Requested incumbent matched leaderboard incumbent: `True`.
- Leaderboard iteration and validation primary scores matched their cached artifacts.
- Fingerprint checks matched the fixed data path, target variables, lead days `1..15`, and protocols `iteration` and `validation`.
- Current HEAD is `3fdb5437dfb22b191c9776a06ae6f0e537b75d2f` and leaderboard eval-code commit is `d187308d30a242bf38aabe5b7eb530fca522a68f`.
- Changed paths since the leaderboard eval commit were limited to dycore model, registry, and dycore tests. No fixed evaluator, protocol, target-variable, lead-time, split, metric, or leaderboard changes were used to invalidate the incumbent cache.
- Candidate source and side-by-side registry edits were not treated as incumbent-cache invalidation, per `roles/PROTOCOL.md` and `roles/SCORER.md`.

## Diagnostics And Guardrails

- Fast candidate diagnostics: failed `False`, issues `0`.
- Iteration candidate diagnostics: failed `False`, issues `0`.
- Cached incumbent iteration diagnostics: failed `False`, issues `0`.
- Worst iteration single-lead RMSE regression: `10m_u_component_of_wind` at `24` hours, relative `0.0006088288912797385`.
- Best iteration single-lead RMSE movement: `geopotential_500` at `24` hours, relative `-2.6943208725330466e-05`.

## Anomalies

- Two registration-check commands used nonexistent helper names and exited with status 1 before the correct `dycore_model_names` helper confirmed both models are registered and instantiable. No files or protocols were changed by those attempts.
- An initial guardrail inspection accidentally allowed persistence rows to overwrite evaluated-model rows. That diagnostic was discarded. The final `scores.json` guardrails filter records by `model_name == dino_ri2m_ekman_tcenter` and `model_name == dino_ri2m_ekman_coupled`.
- A read-only `ps -C python` check returned exit status 1 because no python-named process matched; `nvidia-smi` showed all four GPUs at 100% utilization, so the long iteration run was treated as compute-bound rather than hung.

## Lessons

- The time-centered Ekman source diagnostics were numerically stable and produced clean diagnostics, but the iteration primary score regressed slightly relative to the cached incumbent.
- Future scorer scripts should always filter evaluation records by model name because each artifact includes both evaluated-model and persistence rows.

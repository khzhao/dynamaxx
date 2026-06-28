# Scoring Notes

## Gate Status

- Fast gate: passed by compatible artifact verification. `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_q_dfi_bypass.json` has exact candidate `model_name`, case `fast`, `failed=false`, `issues=0`, `records=120`, and primary score `-1.123286978926717`.
- Iteration promotion gate: failed. Candidate iteration primary score was `-1.1439754503896644`; incumbent iteration primary score was `-1.143975258592661`; delta was `-1.9179700339044814e-07`, below the required `+0.002`.
- Validation acceptance gate: not run. Validation was allowed only if the iteration gate passed.
- Golden: not run, as required by the protocol and Orchestrator instructions.

## Iteration Guardrails

- Diagnostics were clean for both candidate and incumbent iteration artifacts: candidate `failed=false`, `issues=0`; incumbent `failed=false`, `issues=0`.
- Exact filtering was used before comparison: candidate artifact contained `60` evaluated candidate rows and `60` persistence rows; incumbent artifact contained `60` evaluated incumbent rows and `60` persistence rows. Persistence rows were excluded from all guardrail calculations.
- Early day 1-5 mean RMSE relative changes: `geopotential_500` `+0.000656%`, `mean_sea_level_pressure` `+0.000005%`, `10m_u_component_of_wind` `+0.000004%`, and `2m_temperature` `-0.000001%`. No early mean RMSE regression exceeded the 2% guardrail.
- Variable+lead RMSE guardrail passed. The largest single variable+lead RMSE regression was `geopotential_500` at `24h`: `+0.007681%` (`263.891531665315` candidate RMSE versus `263.8712637418557` incumbent RMSE), below the 10% threshold.
- Short-lead `geopotential_500` was the main sensitivity: 24h `+0.007681%`, 48h `+0.000741%`, 72h `+0.000153%`, 96h `-0.000011%`, and 120h `-0.000049%`.
- Largest single variable+lead improvements were small late `geopotential_500` reductions: 288h `-0.000179%`, 312h `-0.000175%`, 336h `-0.000169%`, and 360h `-0.000144%`.

## Commands And Artifacts

- `uv run python - <<'PY' ... registry check ... PY`: exit `0`; confirmed candidate and incumbent are registered and construct with exact names.
- `uv run pytest`: exit `0`; `130 passed, 2 skipped in 66.10s`.
- `uv run python - <<'PY' ... fast artifact verification ... PY`: exit `0`; reused compatible candidate fast artifact.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_q_dfi_bypass --workers 4`: exit `0`; fresh run with `cached=0`, `pending=229`; wrote `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_q_dfi_bypass.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_q_dfi_bypass.csv`.
- `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_q_dfi_bypass --workers 4`: not run because iteration did not promote.

## Measurement Lessons

- Restoring passive humidity after DFI was numerically stable and almost neutral against the incumbent, but the measured primary delta was slightly negative rather than above the promotion threshold.
- The loss was not a guardrail failure: all fixed RMSE guardrails passed by wide margins, and the largest short-lead `geopotential_500` regression was only `+0.007681%` at 24h.
- Future humidity-only proposals should justify a score-relevant mechanism beyond preserving passive tracer detail, because this candidate changed the aggregate score only at near-roundoff scale and did not improve the fixed target metrics enough to matter.

## Anomalies

- Cache reuse: candidate fast artifact was reused after exact compatibility checks; incumbent iteration and validation artifacts from the leaderboard were reused. Candidate iteration was a fresh run with `cached=0`.
- Resource limits: none observed. Iteration used 4 effective GPU workers across 4 GPUs.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by fast or iteration diagnostics.

## Recommendation To Orchestrator

Report the measured gate status: fast passed, iteration did not promote to validation because primary delta was `-1.9179700339044814e-07`, below `+0.002`. Guardrails and diagnostics were clean. This scorer report does not accept or reject the candidate.

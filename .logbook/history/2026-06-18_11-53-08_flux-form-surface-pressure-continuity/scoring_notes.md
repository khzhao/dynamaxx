# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_flux_form_logp` exited 0 with `failed=false`, `issues=0`, and primary score `-1.103563944101271`.
- Iteration promotion gate: did not promote to validation. Candidate iteration primary score was `-1.139320455742976`; incumbent iteration primary score was `-1.1241936221835356`; delta was `-0.015126833559440334`, below the required `+0.002`.
- Iteration diagnostics and guardrails: clean diagnostics (`failed=false`, `issues=0`), no early day 1-5 mean RMSE regressions over 2%, and no variable+lead RMSE regressions over 10%.
- Validation acceptance gate: not evaluated. Validation was not run because the iteration promotion gate failed.

## Measurement Lessons

- The flux-form log-pressure continuity correction was numerically stable on fast and iteration protocols but reduced the fixed iteration primary score relative to the Strang incumbent.
- The negative primary movement occurred without diagnostic failures or guardrail RMSE spikes, which suggests the change broadly degraded scored skill rather than causing an isolated instability.
- Raw metric JSON includes `persistence` baseline records; scorer comparisons filtered records by the evaluated `model_name` before computing guardrails.

## Anomalies

- Cache reuse: incumbent iteration and validation artifacts were reused from the provided leaderboard-compatible paths. Candidate iteration reported `cached=0` for 229 chunks.
- Resource limits: no resource limit was hit. Iteration used 4 requested workers, 4 effective GPU workers, and 4 visible GPUs according to the evaluation command output.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by fast or iteration diagnostics.

## Recommendation To Orchestrator

Report the measured gate status and caveats above. Do not accept or reject the candidate here.

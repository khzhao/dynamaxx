# Scoring Notes

## Gate Status

- Fast gate: passed. Reused compatible fast artifact for `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_surface_diag` with `failed=false`, `issues=0`, `records=120`, and primary score `-1.2277670746969804`.
- Iteration promotion gate: failed. Candidate primary `-1.245126054186803` versus incumbent primary `-1.143975258592661` gives delta `-0.10115079559414197`, below the required `+0.002`.
- Iteration diagnostics: clean. Candidate iteration reported `failed=false`, `issues=0`, `records=120`.
- Early day 1-5 mean RMSE guardrail: failed. Worst relative regression was `10m_u_component_of_wind` at `9.833722%`, above the `2%` limit.
- Variable+lead RMSE guardrail: failed. Worst relative regression was `10m_u_component_of_wind` at `24h`, `16.538051%`, above the `10%` limit.
- Validation acceptance gate: not evaluated because the iteration gate did not promote.

## Measurement Lessons

- The output-only surface diagnostic extrapolation made the sanity-fast score much worse and the fixed iteration score substantially worse, driven by the same scored near-surface channels it targeted.
- `10m_u_component_of_wind` degraded most sharply at early lead: day 1 RMSE increased from `5.455615913305551` to `6.357868482420393`.
- `2m_temperature` also failed the early mean guardrail with `5.789438%` relative RMSE regression over days 1-5.
- Dynamical fields stayed effectively unchanged as expected for an output-only candidate: short-lead `geopotential_500` relative changes stayed near zero, and MSLP changes were also negligible.

## Anomalies

- Cache reuse: reused compatible incumbent iteration and validation artifacts from the leaderboard; reused compatible candidate fast artifact; candidate iteration was fresh with `cached=0` and `pending=229`.
- Resource limits: no resource failures observed with `--workers 4`.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by fast or iteration diagnostics.
- Golden: not run, as required.

## Recommendation To Orchestrator

Report the measured gate status and caveats only. The candidate did not promote to validation; Orchestrator retains accept/reject authority and cleanup ownership.

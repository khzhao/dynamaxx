# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_sigma_hydro_init` exited 0 with `failed=False`, `issues=0`, and primary score `-1.105824620243784`.
- Iteration promotion gate: did not pass. Candidate iteration primary score was `-1.1325393662110732` versus incumbent `-1.1241936221835356`, for a delta of `-0.008345744027537627`, below the required `+0.002`.
- Validation acceptance gate: not evaluated. Candidate validation was skipped because the iteration promotion gate did not pass.

## Measurement Lessons

- Raw iteration CSVs contain persistence rows as well as evaluated-model rows. Guardrails were computed after filtering by the evaluated `model_name`, leaving 60 model rows per iteration artifact from 120 raw rows.
- The candidate had clean diagnostics and did not trip either RMSE guardrail, but it still worsened the primary iteration score. Primary score gating remains the decisive promotion criterion here.
- The largest early day 1-5 mean RMSE increase was `1.0896092728062252%` for `2m_temperature`; the largest single variable-lead RMSE increase was `1.1587809049258489%` for `geopotential_500` at day 1. Both are below the configured guardrails.

## Anomalies

- Cache reuse: incumbent iteration and validation artifacts were reused from `outputs/eval/`. Candidate fast was rerun under Scorer policy, overwriting the existing fast artifact at the same path. Candidate iteration reported `cached=0`.
- Resource limits: none observed. Candidate iteration ran with 4 effective GPU workers.
- Failed or restarted commands: none. `uv run pytest` exited 0 with 147 passed and 2 skipped.
- Nonfinite or unstable outputs: none reported by diagnostics; candidate fast and iteration both had `issues=0`.

## Recommendation To Orchestrator

Report the measured gate status and caveats. The candidate did not promote to validation because the iteration primary score delta was negative; this is a measurement report only, not an accept/reject decision.

# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run pytest` exited 0 with 149 passed and 2 skipped. `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_inertial_surface_residual` exited 0 with `failed=False`, `issues=0`, and primary score `-1.1006322010629643`.
- Iteration promotion gate: did not pass by the measured thresholds. Candidate iteration primary was `-1.1286185780501627`; reused incumbent iteration primary was `-1.1241936221835356`; delta was `-0.004424955866627167`, below the required `+0.002`. Diagnostics were clean (`failed=False`, `issues=0`), and the early day 1-5 mean RMSE regression was only `+0.012352086364009196%`, below the 2% guardrail. The per-variable+lead RMSE guardrail was not clean because `10m_u_component_of_wind` at day 1 regressed by `+12.310765318969419%`.
- Validation acceptance gate: not evaluated. The fixed validation command was not run because validation was allowed only after passing the iteration promotion gate.

## Primary Scores

- Candidate fast: `-1.1006322010629643`
- Candidate iteration: `-1.1286185780501627`
- Incumbent iteration: `-1.1241936221835356`
- Iteration delta: `-0.004424955866627167`
- Candidate validation: not run
- Incumbent validation artifact primary: `-1.1127999773519712`
- Validation delta: not available

## Guardrails

- Early day 1-5 mean RMSE: candidate `438.1067219630818`, incumbent `438.05261332596393`, relative change `+0.00012352086364009196`; this does not exceed the `+0.02` threshold.
- Worst RMSE regression: `10m_u_component_of_wind`, day 1, candidate `6.135131391916096` vs incumbent `5.462638754612658`, relative change `+0.12310765318969419`.
- Other early 10 m zonal wind regressions: day 2 `+2.7822039151822686%`, day 3 `+1.2140106703747655%`, day 4 `+0.5926752747486663%`, day 5 `+0.3179970312600755%`.
- Notable improvements were tiny and late-lead: best relative RMSE improvement was `geopotential_500` day 13 at `-0.0018097285718998712%`; this is too small to offset the primary and day 1 wind regression.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_inertial_surface_residual.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_inertial_surface_residual.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_inertial_surface_residual.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_inertial_surface_residual.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.csv`
- Incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.json`
- Incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.csv`

## Measurement Lessons

- The candidate primarily worsened early `10m_u_component_of_wind`, especially day 1. This is consistent with the risk that the accepted fixed-component residual is acting more like a stationary zonal bias correction than an inertially rotating ageostrophic residual.
- Mass-field metrics were effectively neutral. The largest listed mass-field changes were late-lead improvements at less than `0.002%` relative RMSE, so the output-only implementation did not show a material mass-field disturbance in iteration.
- The metric JSON contains both evaluated-model records and persistence records. Candidate-vs-incumbent guardrails were computed only from records whose `model_name` matched the evaluation result `model_name`.

## Anomalies

- Cache reuse: candidate iteration reported `cached=0`; incumbent iteration and validation artifacts were reused from the Orchestrator-provided paths.
- Resource limits: none observed. Iteration used 4 effective GPU workers on 4 GPUs with worker devices `0:0,1:1,2:2,3:3`.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by diagnostics.
- Worktree state: scoring ran on a dirty worktree containing the candidate implementation changes; no source files were edited by the Scorer.

## Recommendation To Orchestrator

Use the measured gate status above. The Scorer is not accepting or rejecting the candidate.

# Scoring Notes

## Gate Status

- Registration check: passed. Both candidate and incumbent were present in `dycore_model_names()`.
- Fast gate: passed. `uv run pytest` exited 0 with 147 passed and 2 skipped. `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_var_interp_init` exited 0 with `failed=False`, `issues=0`, and primary score `-1.102051740997463`.
- Iteration promotion gate: did not pass. Candidate iteration primary was `-1.1293266929843402`; reused incumbent iteration primary was `-1.1241936221835356`; delta was `-0.005133070800804607`, below the required `+0.002`.
- Iteration diagnostics were clean: candidate `failed=False`, `issues=0`; reused incumbent `failed=False`, `issues=0`.
- Iteration RMSE guardrails were clean. The early day 1-5 mean RMSE relative regression was `+0.28756168845514457%` overall, and the worst per-variable early mean regression was `geopotential_500` at `+0.3729611246919541%`, below the `+2%` limit. No variable+lead RMSE regression exceeded `+10%`.
- Validation acceptance gate: not evaluated. The fixed validation command was not run because validation was allowed only after the candidate passed the iteration promotion gate.

## Primary Scores

- Candidate fast: `-1.102051740997463`
- Candidate iteration: `-1.1293266929843402`
- Incumbent iteration: `-1.1241936221835356`
- Iteration delta: `-0.005133070800804607`
- Candidate validation: not run
- Incumbent validation artifact primary: `-1.1127999773519712`
- Validation delta: not available

## Guardrails

- Early day 1-5 mean RMSE: candidate `439.31228481716596`, incumbent `438.05261332596393`, relative change `+0.0028756168845514457`; this does not exceed the `+0.02` threshold.
- Worst early day 1-5 per-variable mean RMSE regression: `geopotential_500`, candidate `738.6477986790251`, incumbent `735.903165954637`, relative change `+0.003729611246919541`.
- Worst variable+lead RMSE regression: `geopotential_500`, day 1, candidate `264.63880143873547` vs incumbent `261.47464776901603`, relative change `+0.012101187234468024`.
- Per-variable+lead RMSE regressions over `+10%`: none.
- Notable improvements: none. No target variable and lead had lower candidate RMSE than the incumbent in the iteration comparison.

## Worst Regressions

| Variable | Lead day | Candidate RMSE | Incumbent RMSE | Relative change |
| --- | ---: | ---: | ---: | ---: |
| `geopotential_500` | 1 | `264.63880143873547` | `261.47464776901603` | `+1.2101187234468025%` |
| `mean_sea_level_pressure` | 7 | `1952.595031787163` | `1945.0073043615325` | `+0.3901130555456276%` |
| `mean_sea_level_pressure` | 8 | `2114.1778011600286` | `2106.14671632582` | `+0.3813164948080633%` |
| `10m_u_component_of_wind` | 12 | `14.778650594065526` | `14.724005028495633` | `+0.3711324837511079%` |
| `geopotential_500` | 7 | `1524.5627785246006` | `1519.0329519076865` | `+0.36403598815742694%` |

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_var_interp_init.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_var_interp_init.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_var_interp_init.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_var_interp_init.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.csv`
- Incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.json`
- Incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang.csv`

## Anomalies And Resource Notes

- Cache reuse: candidate iteration reported `cached=0`; incumbent iteration and validation artifacts were reused from the Orchestrator-provided paths.
- Resource limits: none observed. Iteration used 4 effective GPU workers on 4 GPUs with worker devices `0:0,1:1,2:2,3:3`.
- Failed or restarted fixed commands: none.
- Nonfinite or unstable outputs: none reported by diagnostics.
- Worktree state: scoring ran on a dirty worktree containing the candidate implementation changes; no source files were edited by the Scorer.
- Candidate fast was rerun under Scorer policy and wrote over the existing candidate fast artifact path.

## Measurement Lessons

- The candidate broadly worsened target RMSE in iteration: no target variable and lead improved relative to the incumbent.
- The worst RMSE changes were still below fixed guardrails, so the measured blocker is the primary-score regression rather than diagnostics or RMSE guardrail failure.
- The result is evidence against pressure-linear scalar initialization for this Strang incumbent; the accepted all-log-pressure initialization remains stronger under this fixed iteration protocol.

## Recommendation To Orchestrator

Use the measured gate status above. The Scorer is not accepting or rejecting the candidate.

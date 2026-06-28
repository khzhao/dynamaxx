# Scoring Notes

## Gate Status

- Fast gate: passed by verified existing artifact `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init.json`; model name matched the candidate, case was `fast`, records=120, diagnostics failed=false, issues=0, primary score=-1.1846413205137396.
- Iteration promotion gate: passed as measured. Candidate primary=-1.2155220438349765, incumbent primary=-1.2218408656785489, delta=+0.006318821843572353 versus the +0.002 threshold. Candidate and incumbent diagnostics were clean. No early mean RMSE regression exceeded 2%; no variable+lead RMSE regression exceeded 10%.
- Validation acceptance gate: passed as measured. Candidate primary=-1.2028991078287248, incumbent primary=-1.2103467803549615, delta=+0.007447672526236682 versus the +0.001 threshold. Candidate and incumbent diagnostics were clean. No early mean RMSE regression exceeded 2%; no variable+lead RMSE regression exceeded 10%.
- Decision note: this file reports measurements only. Accept/reject authority remains with the Orchestrator.

## Command Details

- `uv run python -c "from dynamaxx.dycore.registry import dycore_model_names; ..."` exited 0 at 2026-06-17T00:57:21Z and confirmed candidate_registered=True and incumbent_registered=True.
- `uv run pytest` exited 0; started 2026-06-17T00:56:25Z; result `109 passed, 2 skipped in 54.17s`.
- Candidate fast eval was verified from the existing artifact rather than rerun. The verification command exited 0 and confirmed clean diagnostics and compatible case/model metadata.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init --workers 4` exited 0; started 2026-06-17T00:57:27Z; wrote `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init.json` and `.csv`; result failed=false, issues=0, records=120, primary_score=-1.2155220438349765.
- `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init --workers 4` exited 0; started 2026-06-17T01:42:51Z; wrote `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init.json` and `.csv`; result failed=false, issues=0, records=120, primary_score=-1.2028991078287248.

## RMSE Guardrails

- Iteration early-lead mean RMSE relative regressions: `10m_u_component_of_wind`=-3.4934173271728687e-10, `2m_temperature`=1.760833545712427e-10, `geopotential_500`=1.9145198230944963e-10, `mean_sea_level_pressure`=6.206355366859099e-10.
- Iteration max variable+lead RMSE regression: `mean_sea_level_pressure` at lead 336h, relative_regression=3.149295169632352e-09.
- Validation early-lead mean RMSE relative regressions: `10m_u_component_of_wind`=1.932506154951697e-09, `2m_temperature`=-2.2352293831217008e-10, `geopotential_500`=3.1300849219243315e-10, `mean_sea_level_pressure`=-4.6441325368699556e-10.
- Validation max variable+lead RMSE regression: `10m_u_component_of_wind` at lead 120h, relative_regression=3.874032906601613e-09.

## Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init.csv`
- Candidate validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init.json`
- Candidate validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs.csv`
- Incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs.json`
- Incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs.csv`

## Anomalies

- Cache reuse: existing candidate fast and incumbent iteration/validation artifacts were reused after metadata and diagnostics checks; candidate iteration and validation were fresh runs with cached=0.
- Resource notes: both long evals used GPU dispatch with requested_workers=4, effective_workers=4, gpu_count=4.
- Auxiliary command issues: an initial registration check imported a non-existent `registered_model_names` helper and exited 1; the corrected registry command using `dycore_model_names` exited 0. A later auxiliary protocol metadata query imported a non-existent `get_eval_case` helper and exited 1; protocol metadata was taken from eval artifacts and `src/dynamaxx/eval/protocols.py`.
- Nonfinite or unstable outputs: none reported by diagnostics.

## Measurement Lessons

- The log-pressure initialization candidate changes primary score materially while RMSE differences versus the incumbent are near numerical roundoff across both iteration and validation guardrails.
- The registry and protocol modules expose `dycore_model_names` and `create_case`; future scoring helper snippets should use those exact helper names to avoid auxiliary ImportError noise.

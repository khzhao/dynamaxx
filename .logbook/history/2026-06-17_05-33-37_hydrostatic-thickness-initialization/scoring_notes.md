# Scoring Notes: hydrostatic-thickness-initialization

## Scope

Scored candidate `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init` against incumbent `dinosaur_dfi_surface_residual_weak_hs_logp_init` as the Scorer role. I did not change dycore source, tests, evaluation code, fixed metrics, splits, lead times, target variables, or proposals. I did not run `golden` and did not make an accept/reject decision.

## Commands

| Step | Command | Exit | Result |
| --- | --- | ---: | --- |
| Registration | `python - <<'PY' ... create_dycore_model registration check ... PY` | 0 | Candidate and incumbent both registered; constructed model names matched exactly. |
| Tests | `uv run pytest` | 0 | 116 passed, 2 skipped in 58.49s. |
| Fast/artifact verification | `python - <<'PY' ... verify existing fast/incumbent artifacts ... PY` | 0 | Reused compatible candidate fast and incumbent iteration/validation artifacts. |
| Iteration | `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init --workers 4` | 0 | Completed 229/229 chunks, cached=0; clean diagnostics; wrote candidate iteration JSON/CSV. |
| Validation | `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init --workers 4` | 0 | Completed 46/46 chunks, cached=0; clean diagnostics; wrote candidate validation JSON/CSV. |

## Artifact Reuse And Raw Outputs

- Candidate fast reused: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init.json`, `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init.csv`; primary `-1.11920031385614`, diagnostics failed `False`, issues `0`.
- Incumbent iteration reused: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init.json`, `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init.csv`.
- Incumbent validation reused: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init.json`, `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init.csv`.
- Candidate iteration generated: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init.json`, `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init.csv`.
- Candidate validation generated: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init.json`, `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_init.csv`.

All comparisons filtered metric records by exact evaluated `model_name`, excluding duplicate-key `persistence` rows.

## Iteration Gate

- Candidate primary: `-1.14866422877818`.
- Incumbent primary: `-1.21552204383498`.
- Primary delta: `0.0668578150568`; threshold `+0.002`; pass `true`.
- Diagnostics: candidate failed `false`, candidate issues `0`; incumbent failed `false`, incumbent issues `0`.
- Early day 1-5 mean RMSE: candidate `445.406042059761`, incumbent `458.603234108946`, relative delta `-0.0287769275653424`; no >2% regression.
- Variable+lead RMSE regressions: `3` positive, `0` over 10%.
- Largest variable+lead regression: `2m_temperature` lead `24` h, relative delta `0.0254961599017503`.
- Iteration promotion gate status: `passed`.

## Validation Gate

- Candidate primary: `-1.13549428967014`.
- Incumbent primary: `-1.20289910782873`.
- Primary delta: `0.0674048181585818`; threshold `+0.001`; pass `true`.
- Diagnostics: candidate failed `false`, candidate issues `0`; incumbent failed `false`, incumbent issues `0`.
- Early day 1-5 mean RMSE: candidate `432.677000896762`, incumbent `445.985312068114`, relative delta `-0.0298402454323869`; no >2% regression.
- Variable+lead RMSE regressions: `4` positive, `0` over 10%.
- Largest variable+lead regression: `2m_temperature` lead `24` h, relative delta `0.0219215857304019`.
- Validation gate status: `passed`.

## Resource And Cache Notes

Pre-run resources were 48 CPUs, 174 GiB available memory, and 4.1 TiB available disk on the repository/output/logbook filesystem. Both long evaluations reported GPU dispatch with 4 effective workers across 4 GPUs. Candidate iteration and validation both started with `cached=0`, so timings reflect full candidate evaluation rather than chunk-cache reuse. No command failed, no diagnostics were reported, and no resource anomalies were observed.

## Lessons

The exact `model_name` filter matters: each JSON contains 60 evaluated-model rows and 60 `persistence` rows with duplicate `(channel_name, lead_hours)` keys. The candidate improves primary score and early mean RMSE strongly while only introducing small short-lead 2m-temperature RMSE regressions, all below guardrail thresholds.

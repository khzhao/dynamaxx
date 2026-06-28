# Scoring Notes

## Gate Status

- Fast gate: passed using the pre-existing authorized fast artifact. Candidate fast primary_score=-0.7990725366440742, failed=False, issues=0, records=120.
- Registration gate: passed. Both the candidate and incumbent were constructible via `create_dycore_model()`. The incumbent has `use_monotone_surface_layer_10m_wind_diagnostic=False`; the candidate has it true.
- Iteration promotion gate: failed by measurement. Candidate primary_score=-0.8309040873499036; incumbent primary_score=-0.8308832822743712; iteration_delta=-2.0805075532370765e-05, below the +0.002 threshold. Candidate and incumbent diagnostics were clean.
- Iteration early day 1-5 mean RMSE guard: passed. Overall early mean RMSE relative change was 4.0200774984299765e-05%, below the +2% threshold. By variable, 10m_u_component_of_wind changed by -0.00011602011355798114%, 2m_temperature changed by 0.00010101907509498865%, geopotential_500 changed by 0.00010288262109956076%, mean_sea_level_pressure changed by -5.5749833509815e-06%.
- Iteration variable+lead RMSE guard: passed. No variable+lead exceeded the +10% regression threshold; the largest positive variable+lead change was geopotential_500 day 12.0 at 0.009725953842613903%.
- Validation acceptance gate: not run. Validation policy allows validation only if the fixed iteration promotion gates pass; the primary delta gate failed.
- Golden: not run, as required for iterative model selection.

## Cache Reuse

- Incumbent iteration metrics were reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter.csv`.
- Reuse checks: leaderboard incumbent matched the requested incumbent; leaderboard fingerprint data path, protocols, target variables, lead days, and eval_code_commit matched the fixed protocol; committed `src/dynamaxx/eval/` and registry code were unchanged relative to cached eval commit `c359ee1b016ccd92412585997a799a7c644a65c5`; no uncommitted `src/dynamaxx/eval/` changes were present; cached iteration JSON existed and had finite primary_score=-0.8308832822743712.
- The working tree does contain uncommitted side-by-side candidate changes in the Dinosaur adapter/export/registry. The current incumbent factory and constructed incumbent behavior remain unchanged for the monotone option, so the cached incumbent iteration artifact was treated as valid. This caveat is recorded in `scores.json.cache_reuse.conditions`.
- Incumbent validation metrics were verified available at `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter.json` and `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter.csv` but were not used because candidate validation was skipped.

## Measurement Lessons

- The monotone 10 m wind cap did not improve the fixed iteration primary score relative to the theta-mean-recenter incumbent; iteration_delta=-2.0805075532370765e-05.
- The monotone cap produced only tiny RMSE movements in `10m_u_component_of_wind`; day 15 changed by 0.0007052564209255235%, so it did not materially address the previous late-wind limitation.
- The largest variable+lead improvement was 2m_temperature day 11.0 at -0.004264846216198536%; the largest positive variable+lead regression was geopotential_500 day 12.0 at 0.009725953842613903%, still far under the +10% guardrail.
- Since diagnostics and RMSE guardrails were clean but the primary score regressed slightly, future wind-output-only proposals need a stronger mechanism than this monotone scalar cap to move aggregate skill.

## Anomalies

- Candidate validation was skipped by protocol because the iteration primary delta failed the +0.002 promotion threshold.
- Resource limits: none observed. Iteration used 229 chunks with 4 effective GPU workers; CPU count was 48, available RAM was about 174 GiB, four L4 GPUs each reported 22566 MiB free in the resource check, and disk free space was about 4.1T.
- Failed or restarted commands: none for required scoring commands. A read-only `rg` lookup used during context gathering exited 2 after producing useful matches; it did not affect scoring.
- Nonfinite or unstable outputs: none reported. Candidate fast and iteration diagnostics had failed=False and issue_count=0.
- Protocol limits: golden was not run; source code, tests, roles, evaluation protocols, metrics, target variables, data splits, lead times, and leaderboard were not changed by Scorer.

## Recommendation To Orchestrator

Report measured gate status only: fast passed, iteration did not promote to validation, validation was skipped, incumbent iteration was compared from valid cached metrics, and golden was not run. The Scorer does not accept or reject the candidate.

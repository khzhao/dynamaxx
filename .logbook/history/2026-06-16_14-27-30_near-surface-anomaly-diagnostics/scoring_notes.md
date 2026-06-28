# Scoring Notes

## Gate Status

- Fast gate: passed. The Implementer-provided `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual` record exited 0; Scorer verified `outputs/eval/fast_dinosaur_dfi_surface_residual.json` with `primary_score=-1.2475800298776727`, diagnostics `failed=false`, `issues=0`, and `records=120`.
- Iteration promotion gate: passed by the fixed quantitative checks. Candidate iteration primary was `-1.2854136202685928` versus incumbent `-1.3208025947740873`, delta `+0.0353889745054945` against the `+0.002` threshold; diagnostics were clean; no early lead 1-5 mean RMSE regression exceeded 2%; no variable/lead RMSE regression exceeded 10%.
- Validation acceptance gate: passed by the fixed quantitative checks. Candidate validation primary was `-1.2725740410982802` versus incumbent `-1.308334010223954`, delta `+0.03575996912567381` against the `+0.001` threshold; diagnostics were clean; no early lead 1-5 mean RMSE regression exceeded 2%; no variable/lead RMSE regression exceeded 10%.

Scorer reports measured gate status only. Accept, reject, or revision authority remains with the Orchestrator.

## Commands And Artifacts

- Registration check: `uv run python -c "from dynamaxx.dycore.registry import dycore_model_names; names=set(dycore_model_names()); print('dinosaur_dfi_surface_residual', 'registered' if 'dinosaur_dfi_surface_residual' in names else 'missing'); print('dinosaur_dfi', 'registered' if 'dinosaur_dfi' in names else 'missing'); raise SystemExit(0 if {'dinosaur_dfi_surface_residual','dinosaur_dfi'} <= names else 1)"` exited 0.
- Candidate iteration: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual --workers 4` exited 0, started `2026-06-16T14:28:33Z`, finished `2026-06-16T15:07:00Z`, wrote `outputs/eval/iteration_dinosaur_dfi_surface_residual.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual.csv`.
- Candidate validation: `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual --workers 4` exited 0, started `2026-06-16T15:07:30Z`, finished `2026-06-16T15:16:20Z`, wrote `outputs/eval/validation_dinosaur_dfi_surface_residual.json` and `outputs/eval/validation_dinosaur_dfi_surface_residual.csv`.
- Incumbent iteration artifacts reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dinosaur_dfi.json` and `outputs/eval/iteration_dinosaur_dfi.csv`.
- Incumbent validation artifacts reused from `.logbook/leaderboard.json`: `outputs/eval/validation_dinosaur_dfi.json` and `outputs/eval/validation_dinosaur_dfi.csv`.

## RMSE Regression Checks

- Corrected Orchestrator check compared only candidate and incumbent model rows, excluding persistence rows in the evaluation artifacts.
- Iteration early lead 1-5 mean RMSE regressions: `10m_u_component_of_wind=-1.6865131442274195%`, `2m_temperature=-10.160379592638602%`, `geopotential_500=-5.988478379848061e-07%`, `mean_sea_level_pressure=-8.007358998085579e-07%`.
- Validation early lead 1-5 mean RMSE regressions: `10m_u_component_of_wind=-1.6811456695807636%`, `2m_temperature=-10.173883197202226%`, `geopotential_500=-5.118736214893005e-05%`, `mean_sea_level_pressure=-1.2185058884117694e-05%`.
- Iteration max per-variable/lead RMSE regressions: `10m_u_component_of_wind` day 15 `-0.0016226914907657708%`, `2m_temperature` day 15 `-0.010280825803210547%`, `geopotential_500` day 12 `4.877946713222059e-06%`, `mean_sea_level_pressure` day 12 `6.2908864784105845e-06%`.
- Validation max per-variable/lead RMSE regressions: `10m_u_component_of_wind` day 15 `-0.0014483723411506944%`, `2m_temperature` day 15 `-0.010540227043731587%`, `geopotential_500` day 15 `0.00013412959092296006%`, `mean_sea_level_pressure` day 15 `0.00045982695662249995%`.
- Per-variable/lead regressions above 10%: none for iteration or validation.

## Measurement Lessons

- The primary score improved substantially through near-surface channels: day-1 iteration RMSE improved by about 34.7% for `2m_temperature` and 6.5% for `10m_u_component_of_wind`, with similar validation behavior.
- The output-only correction did not measurably degrade pressure-level or mean-sea-level-pressure RMSE in iteration or validation.
- Fresh candidate iteration and validation runs had no cache hits, so the candidate deltas were not produced by stale candidate chunks.

## Anomalies

- Cache reuse: incumbent iteration and validation artifacts were intentionally reused from `.logbook/leaderboard.json`; candidate iteration reported `chunks=229 cached=0`, and candidate validation reported `chunks=46 cached=0`.
- Resource limits: no limiting condition observed. Scoring snapshots showed `/dev/root` with 4.1T available and four NVIDIA L4 GPUs active with about 17.4 GiB used per GPU.
- Failed or restarted commands: none during Scorer-run registration, fast verification, iteration, or validation.
- Nonfinite or unstable outputs: none reported. Candidate fast, iteration, and validation diagnostics all reported `failed=false` and `issues=0`.

## Recommendation To Orchestrator

Fixed scoring found clean diagnostics and passing iteration and validation quantitative gates for `dinosaur_dfi_surface_residual` against `dinosaur_dfi`. The Orchestrator should make the accept/reject/revision decision using these measurements and any policy considerations outside Scorer authority.

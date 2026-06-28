# Scoring Notes

## Gate Status

- Unit tests: passed by Orchestrator handoff; Scorer did not rerun `uv run pytest`. Reported full gate was `244 passed, 2 skipped in 220.06s`.
- Registration: confirmed both `dino_hsl2_mass_dse_ocean_flux_taper` and `dino_hsl2_mass_dse` can be created through `create_dycore_model`.
- Fast gate: passed from existing candidate artifact, not rerun. `outputs/eval/fast_dino_hsl2_mass_dse_ocean_flux_taper.json` has `failed=False`, `issues=0`, `records=120`, `primary_score=-0.28201298547250314`.
- Iteration promotion gate: failed. Candidate iteration primary score was `-0.2801194788322577`; cached incumbent iteration primary score was `-0.2616483974683927`; delta was `-0.018471081363864994`, below the required `+0.002` improvement.
- Validation acceptance gate: not run and not evaluated because the iteration promotion gate failed.

## Commands

- Reused Orchestrator pytest record: `uv run pytest` exit `0`, `244 passed, 2 skipped in 220.06s`.
- Verified existing fast artifact: `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_ocean_flux_taper`; handoff exit `0`, artifact clean.
- Ran candidate iteration: `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_ocean_flux_taper --workers 4`; exit `0`; run directory `outputs/eval/runs/iteration_dino_hsl2_mass_dse_ocean_flux_taper`; completed 229/229 chunks.
- Did not run candidate validation: `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_ocean_flux_taper --workers 4` skipped after iteration gate failure.
- Did not run incumbent fast, iteration, or validation.
- Did not run golden.

## Cache Reuse

- Iteration incumbent cache was reused from the leaderboard pointer: `outputs/eval/iteration_dino_hsl2_mass_dse.json` and `outputs/eval/iteration_dino_hsl2_mass_dse.csv`.
- Iteration cache checks passed: requested incumbent matched `.logbook/leaderboard.json`, protocol included `iteration`, data path matched, target variables matched, lead range matched, eval code commit matched `2c70bb5b77370a074330c2b46954f74f20771f12`, artifacts were readable, primary score was finite, model name matched, diagnostics were clean, and 120 records were present for guardrails.
- Validation incumbent cache was inspected but not used for candidate comparison because candidate validation was not run. The cached validation artifacts were readable and finite at `outputs/eval/validation_dino_hsl2_mass_dse.json` and `outputs/eval/validation_dino_hsl2_mass_dse.csv`.
- Candidate source edits in the current worktree were not treated as incumbent cache invalidation, per protocol.

## Guardrails

- Candidate iteration diagnostics: `failed=False`, issue count `0`.
- Incumbent iteration diagnostics: `failed=False`, issue count `0`.
- Mean RMSE regression over leads 1-5 days:
  - `10m_u_component_of_wind`: `-4.5026931774537715%`
  - `2m_temperature`: `+37.99203594077941%` violation
  - `geopotential_500`: `-15.686790568314027%`
  - `mean_sea_level_pressure`: `-2.166194827878369%`
- Maximum individual variable-lead RMSE regressions:
  - `10m_u_component_of_wind`, lead 216h: `+8.00222601319191%`
  - `2m_temperature`, lead 240h: `+120.01798535077835%` violation
  - `geopotential_500`, lead 216h: `+3.945855593338517%`
  - `mean_sea_level_pressure`, lead 240h: `+34.46242560069296%` violation
- Individual variable-lead RMSE regressions above 10%: 26 total, concentrated in `2m_temperature` and `mean_sea_level_pressure`.

## Anomalies

- Resource limits: none observed. The iteration run used `--workers 4` and dispatched across four GPUs.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by diagnostics.
- Measurement anomalies: none. The iteration run had a long initial compile/startup phase before chunk files appeared, then completed all chunks steadily.

## Measurement Lessons

- The distributed ocean heat flux taper produced clean forecasts numerically, but the full iteration metric was substantially worse than the incumbent.
- The largest regression was in `2m_temperature`, including more than 100% RMSE regression at many medium and long leads and a `+37.99203594077941%` early-lead mean RMSE regression.
- `geopotential_500`, `10m_u_component_of_wind`, and early `mean_sea_level_pressure` RMSE improved on some aggregate checks, but the primary score and guardrails clearly failed.

## Recommendation To Orchestrator

Report this as a measured iteration promotion failure. Validation was correctly skipped, and the incumbent cache was valid and reused; no incumbent rerun was warranted.

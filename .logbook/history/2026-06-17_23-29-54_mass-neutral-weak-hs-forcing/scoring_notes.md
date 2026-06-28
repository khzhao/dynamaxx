# Scoring Notes

## Gate Status

- Registration: candidate and incumbent model names are registered.
- Tests: `uv run pytest` passed with 130 passed, 2 skipped.
- Fast gate: passed. Candidate fast primary score was `-1.1700551126255327`; diagnostics failed=`false`, issues=`0`.
- Iteration promotion gate: did not promote to validation. Candidate iteration primary score was `-1.2018611065751152`; incumbent iteration primary score was `-1.143975258592661`; delta was `-0.05788584798245422`, below the required `+0.002`.
- Iteration diagnostics: candidate failed=`false`, issues=`0`; incumbent failed=`false`, issues=`0`.
- Iteration guardrails: failed. The candidate regressed 2 m temperature mean RMSE over day 1-5 leads by `5.411372769008427%`, above the `2%` guardrail. It also had 2 m temperature variable+lead RMSE regressions above `10%` at lead hours 168, 192, 216, 240, 264, 288, 312, 336, and 360.
- Validation acceptance gate: not evaluated because validation may run only if iteration promotes.
- Golden: not run.

## Commands

| Command | Exit status | Notes |
|---|---:|---|
| `uv run python -c "from dynamaxx.dycore.registry import dycore_model_names; names=set(dycore_model_names()); required={'dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs','dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init'}; missing=sorted(required-names); print('registered=', ','.join(sorted(required))); assert not missing, missing"` | 0 | Confirmed both model names are present. |
| `uv run pytest` | 0 | `130 passed, 2 skipped in 63.68s`. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs` | 0 | Primary `-1.1700551126255327`, diagnostics clean. |
| `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs --workers 4` | 0 | Primary `-1.2018611065751152`, diagnostics clean, 229 chunks, cached=0 at startup. |
| `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs --workers 4` | not run | Skipped because the iteration promotion gate did not pass. |

Supporting provenance commands also exited 0: `git rev-parse HEAD`, `git status --short`, and the WeatherBench2 data-path check. The eval code commit recorded for comparability is `a7833574e9ade1a5271bd8cbef2fa1357465f5a8`.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_mass_neutral_hs.csv`
- Candidate validation JSON/CSV: not produced.
- Incumbent iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`
- Incumbent validation JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json`
- Incumbent validation CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.csv`

## Guardrail Details

Mean RMSE over lead hours 24-120:

| Variable | Candidate | Incumbent | Regression |
|---|---:|---:|---:|
| `10m_u_component_of_wind` | 8.548035641626493 | 8.67161758555166 | -1.4251313864563686% |
| `2m_temperature` | 7.7568711492385605 | 7.358666285692398 | +5.411372769008427% |
| `geopotential_500` | 745.4133287148682 | 746.8278674886182 | -0.18940626553033413% |
| `mean_sea_level_pressure` | 1006.7480027604946 | 1012.9263924182685 | -0.609954455133066% |

Worst variable+lead RMSE regression:

| Variable | Lead hours | Candidate | Incumbent | Regression |
|---|---:|---:|---:|---:|
| `2m_temperature` | 360 | 12.897000639312246 | 10.126270133796323 | +27.361807150182948% |

All variable+lead guardrail failures were for `2m_temperature`: +10.026264173632459% at 168h, +11.749574672767228% at 192h, +13.661622979325895% at 216h, +15.666202936351104% at 240h, +17.81763659989015% at 264h, +20.03548585714505% at 288h, +22.41205855555386% at 312h, +24.865392196881686% at 336h, and +27.361807150182948% at 360h.

## Cache Reuse

- Candidate fast: serial run, no parallel cache.
- Candidate iteration: no prior candidate chunks reused; startup reported `cached=0 pending=229`.
- Incumbent iteration: reused compatible Orchestrator-provided artifacts.
- Incumbent validation: existing compatible artifacts were present and read for provenance, but candidate validation was not run.

## Anomalies

- Failed or restarted commands: none.
- Resource failures: none.
- Nonfinite or unstable outputs: none reported by diagnostics.
- Worktree note: `git status --short` showed candidate implementation source changes before scorer artifact writes. Scorer did not edit source, revert changes, update `.logbook/leaderboard.json`, commit, or run `golden`.

## Measurement Lessons

- The mass-neutral weak Held-Suarez forcing variant produced clean forecasts but materially worsened the primary iteration score relative to the incumbent.
- The regression is concentrated in 2 m temperature, including both early leads and long leads; future variants of this idea should check near-surface temperature response before full iteration scoring.
- The incumbent artifacts were directly reusable for this comparison because the iteration case matched and the Orchestrator provided compatible baseline paths.

## Report To Orchestrator

The measured iteration promotion gate is false, so validation was skipped under the supplied rules. This report does not accept or reject the candidate.

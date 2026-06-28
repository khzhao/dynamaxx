# Scoring Notes

## Gate Status

- Fast gate: passed by verified reuse of `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init.json`; exact candidate `model_name`, `failed=false`, 0 issues, 120 records, primary score `-1.1263396094875242`.
- Iteration promotion gate: did not pass. Candidate iteration primary score was `-1.1507511369682746`; incumbent iteration primary score was `-1.143975258592661`; delta was `-0.006775878375613553`, below the required `+0.002`.
- Validation acceptance gate: not evaluated. Validation was allowed only if the iteration gate passed, so `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init --workers 4` was not run.

## Commands

- `uv run python -c "from dynamaxx.dycore.registry import create_dycore_model, dycore_model_names; candidate='dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init'; incumbent='dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init'; names=set(dycore_model_names()); assert candidate in names and incumbent in names; assert create_dycore_model(candidate).name == candidate; assert create_dycore_model(incumbent).name == incumbent; print('registered_ok')"`: exit 0. Confirmed both candidate and incumbent are registered and instantiate with matching names.
- `uv run pytest`: exit 0. Started `2026-06-17T08:12:56Z`, finished `2026-06-17T08:14:04Z`; 131 passed, 2 skipped in 65.08s.
- `uv run python -c "import json; path='outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init.json'; data=json.load(open(path)); assert data['model_name']=='dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init'; assert data['diagnostics']['failed'] is False; assert len(data['diagnostics']['issues']) == 0; assert len(data['records']) == 120; print('fast_artifact_ok')"`: exit 0. Reused the Implementer fast artifact after checking exact candidate `model_name`, diagnostics, and records.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init --workers 4`: exit 0. Started `2026-06-17T08:14:24Z`, finished `2026-06-17T08:59:31Z`; `failed=False`, issues 0, records 120, primary score `-1.1507511369682746`.
- `uv run python -c "import json; candidate='dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init'; incumbent='dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init'; cd=json.load(open('outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_conservative_init.json')); id=json.load(open('outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init.json')); cr=[r for r in cd['records'] if r['model_name']==candidate]; ir=[r for r in id['records'] if r['model_name']==incumbent]; assert len(cr)==60 and len(ir)==60; assert sum(1 for r in cd['records'] if r['model_name']=='persistence')==60; assert sum(1 for r in id['records'] if r['model_name']=='persistence')==60; print(cd['primary_score'] - id['primary_score'])"`: exit 0. Candidate and incumbent comparisons used only rows whose `model_name` exactly matched the evaluated model.

## Diagnostics And Guardrails

- Candidate iteration diagnostics: `failed=false`, issue count 0.
- Incumbent iteration diagnostics: `failed=false`, issue count 0.
- Early day 1-5 mean RMSE guardrail: clean. Worst relative change was `geopotential_500` at `+1.039093269800594%`, below the 2% limit.
- Variable+lead RMSE guardrail: clean. Worst relative change was `geopotential_500` at lead 168 hours, `+1.68997781487689%`, below the 10% limit.
- Record filtering: both candidate and incumbent iteration artifacts contained 60 exact evaluated-model rows and 60 persistence rows. Persistence rows were excluded before joining by `(channel_name, lead_hours)`.

## Measurement Lessons

- The conservative initialization remap produced clean forecasts but reduced iteration primary score. Its largest RMSE increases were concentrated in `geopotential_500` and `mean_sea_level_pressure` around days 4-8, which is consistent with a remap that smooths or perturbs column structure enough to hurt medium-lead mass-field evolution.
- The exact-model filtering caution was material: each eval artifact had persistence rows with duplicate `(channel_name, lead_hours)` keys, so any dictionary keyed only by variable and lead would have overwritten evaluated-model rows.

## Anomalies

- Cache reuse: reused the Implementer fast candidate artifact after verification. Candidate iteration was run from scratch with `cached=0`; incumbent iteration and validation artifacts were reused from the compatible leaderboard paths supplied by the Orchestrator.
- Resource limits: none observed. Iteration used 4 workers with GPU dispatch across 4 devices.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by diagnostics.

## Recommendation To Orchestrator

Measured gate status only: fast passed, iteration did not promote to validation because the primary-score delta was negative, and validation was skipped under the fixed protocol.

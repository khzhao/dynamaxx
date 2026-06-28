# Scoring Notes

Scorer role for iteration 20, candidate `dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output` against incumbent `dinosaur_dfi_surface_residual_weak_hs_logp_init`.

## Commands

- `uv run python - <<'PY' ... create_dycore_model/dycore_model_names check ... PY`: exit 0; both candidate and incumbent are registered and constructible.
- `uv run pytest`: exit 0; 115 passed, 2 skipped in 58.46s.
- `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output`: exit 0; failed=False, issues=0, records=120, primary_score=-1.183048237985.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output --workers 4`: exit 0; failed=False, issues=0, records=120, primary_score=-1.213880820532.
- Validation command was not run because the iteration promotion gate failed.

## Artifact Paths

- Candidate fast JSON/CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output.json`, `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output.csv`
- Candidate iteration JSON/CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output.json`, `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_logp_output.csv`
- Incumbent iteration JSON/CSV reused: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init.json`, `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init.csv`
- Incumbent validation JSON/CSV available but not used for candidate acceptance: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init.json`, `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs_logp_init.csv`

## Iteration Gate

- Primary score: candidate -1.213880820532, incumbent -1.215522043835, delta +0.001641223303; required delta is >= +0.002, so primary threshold pass is False.
- Candidate iteration diagnostics: failed=False, issues=0; diagnostics pass is True.
- Early mean RMSE regressions >2% for lead days 1-5: 0; pass is True.
- Variable+lead RMSE regressions >10%: 54; pass is False.
- Overall iteration promotion gate pass: False.

Early mean RMSE by lead day:
- Day 1: incumbent 238.622257, candidate 238.629365, relative delta +0.002979%.
- Day 2: incumbent 366.359657, candidate 366.172041, relative delta -0.051211%.
- Day 3: incumbent 459.936719, candidate 459.630031, relative delta -0.066681%.
- Day 4: incumbent 538.619152, candidate 538.077535, relative delta -0.100557%.
- Day 5: incumbent 607.618560, candidate 606.975002, relative delta -0.105915%.

Largest variable+lead RMSE regressions:
- 2m_temperature lead 168h: incumbent 3.370708, candidate 10.746226, relative delta +218.812106%.
- 2m_temperature lead 144h: incumbent 3.296513, candidate 10.453283, relative delta +217.101228%.
- 2m_temperature lead 192h: incumbent 3.436663, candidate 10.871052, relative delta +216.325778%.
- 2m_temperature lead 216h: incumbent 3.490733, candidate 10.937837, relative delta +213.339248%.
- 2m_temperature lead 120h: incumbent 3.211934, candidate 9.929086, relative delta +209.131077%.
- 2m_temperature lead 240h: incumbent 3.539439, candidate 10.931565, relative delta +208.850236%.
- 2m_temperature lead 264h: incumbent 3.586266, candidate 10.882948, relative delta +203.461851%.
- 2m_temperature lead 288h: incumbent 3.627973, candidate 10.777788, relative delta +197.074671%.

## Resource, Cache, And Anomaly Notes

- Resource check before scoring showed 48 CPUs, about 174 GiB available RAM, and about 4.1 TiB free disk, compatible with the requested 4 workers.
- Candidate iteration started with `cached=0 pending=229`, so it was a fresh full iteration run rather than reuse of prior candidate chunks.
- Existing incumbent iteration and validation artifacts were reused after model-name/schema compatibility checks.
- An initial exploratory registration probe used a non-existent `available_models` helper and exited 1; the corrected registry check using `dycore_model_names` and `create_dycore_model` exited 0. This did not affect scoring.
- Validation was skipped because the candidate did not pass iteration promotion; no acceptance decision is made by Scorer.

## Lessons

- The candidate slightly improves aggregate iteration primary score but substantially worsens many per-variable lead RMSE values, especially 2m temperature, 10m wind, mean sea-level pressure, and geopotential at later leads.
- Future proposals involving log-pressure output interpolation should inspect variable-specific scaling/units and lead-dependent behavior before committing to full validation runs.

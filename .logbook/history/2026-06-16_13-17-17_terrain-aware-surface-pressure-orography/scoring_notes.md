# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate fast primary `-1.0905432571118128`; diagnostics failed `false`; issues `0`; raw metrics `outputs/eval/fast_dinosaur_dfi_terrain.json` and `outputs/eval/fast_dinosaur_dfi_terrain.csv`.
- Iteration promotion gate: failed. Candidate primary `-1.122351043157642` versus incumbent `-1.3208025947740873` gives delta `0.19845155161644534`, which passes the `+0.002` primary threshold, and diagnostics failed `false` with issues `0`. The RMSE guardrails fail: early lead 1-5 mean RMSE regression is `36.02191018071786%` for `geopotential_500` and `32.23194296316327%` for `mean_sea_level_pressure`; there are `8` per-variable/lead RMSE regressions over `10%`.
- Validation acceptance gate: failed as measured, but the validation run was not protocol-allowed after the corrected iteration gate. Candidate primary `-1.126083021438326` versus incumbent `-1.308334010223954` gives delta `0.18225098878562807`, and diagnostics failed `false` with issues `0`. The validation RMSE guardrails fail: early lead 1-5 mean RMSE regression is `38.698233090354485%` for `geopotential_500` and `35.42702633762196%` for `mean_sea_level_pressure`; there are `8` per-variable/lead RMSE regressions over `10%`.

## Commands And Raw Metrics

- Registration check: `uv run python -c "from dynamaxx.dycore.registry import dycore_model_names; names=dycore_model_names(); print('\n'.join(names)); assert 'dinosaur_dfi_terrain' in names; assert 'dinosaur_dfi' in names"` exited `0`.
- Provided focused tests: `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` exited `0` with `31 passed`.
- Provided full tests: `uv run pytest` exited `0` with `97 passed, 2 skipped`.
- Provided fast gate: `uv run dynamaxx-eval fast --model dinosaur_dfi_terrain` exited `0`; verified artifact primary `-1.0905432571118128`.
- Scorer iteration: `uv run dynamaxx-eval iteration --model dinosaur_dfi_terrain --workers 4` exited `0`; started `2026-06-16T13:18:12Z`; finished `2026-06-16T13:56:29Z`; raw metrics `outputs/eval/iteration_dinosaur_dfi_terrain.json` and `outputs/eval/iteration_dinosaur_dfi_terrain.csv`.
- Scorer validation: `uv run dynamaxx-eval validation --model dinosaur_dfi_terrain --workers 4` exited `0`; started `2026-06-16T13:56:55Z`; finished `2026-06-16T14:05:44Z`; raw metrics `outputs/eval/validation_dinosaur_dfi_terrain.json` and `outputs/eval/validation_dinosaur_dfi_terrain.csv`.
- Incumbent iteration artifacts reused: `outputs/eval/iteration_dinosaur_dfi.json` and `outputs/eval/iteration_dinosaur_dfi.csv`; incumbent primary `-1.3208025947740873`; diagnostics failed `false`; issues `0`.
- Incumbent validation artifacts reused: `outputs/eval/validation_dinosaur_dfi.json` and `outputs/eval/validation_dinosaur_dfi.csv`; incumbent primary `-1.308334010223954`; diagnostics failed `false`; issues `0`.

## RMSE Guardrail Details

### Iteration Early Lead 1-5 Mean RMSE

| Channel | Candidate | Incumbent | Change |
| --- | ---: | ---: | ---: |
| `2m_temperature` | 7.6203754510458195 | 8.689986167882589 | -12.308543375937179% |
| `mean_sea_level_pressure` | 1398.6253275223248 | 1057.7061004933953 | 32.23194296316327% |
| `geopotential_500` | 1042.6375941388342 | 766.5217998729707 | 36.02191018071786% |
| `10m_u_component_of_wind` | 8.72233991696028 | 9.349176066143551 | -6.7047207662849715% |

### Iteration Per-Lead Regressions Over 10%

| Channel | Lead days | Candidate RMSE | Incumbent RMSE | Change |
| --- | ---: | ---: | ---: | ---: |
| `mean_sea_level_pressure` | 1 | 1128.7018478968585 | 429.38519845404994 | 162.8646380826853% |
| `mean_sea_level_pressure` | 2 | 1242.0917083226582 | 771.6253689595138 | 60.97082318554888% |
| `mean_sea_level_pressure` | 3 | 1388.7193064682733 | 1089.1135792717932 | 27.509135217724808% |
| `mean_sea_level_pressure` | 4 | 1542.608018020707 | 1371.6849143958539 | 12.46081383785829% |
| `geopotential_500` | 1 | 836.1505028833446 | 270.5476486321413 | 209.05849934783322% |
| `geopotential_500` | 2 | 904.7581572501152 | 522.7938720208335 | 73.06211982799606% |
| `geopotential_500` | 3 | 1016.1306349808864 | 779.2085164466295 | 30.405483709890184% |
| `geopotential_500` | 4 | 1156.0053343165146 | 1021.4823277034776 | 13.169391477919639% |

### Validation Early Lead 1-5 Mean RMSE

| Channel | Candidate | Incumbent | Change |
| --- | ---: | ---: | ---: |
| `2m_temperature` | 7.577131634660164 | 8.69254790597424 | -12.831867979093564% |
| `mean_sea_level_pressure` | 1390.3741700743942 | 1026.6593069895569 | 35.42702633762196% |
| `geopotential_500` | 1036.7039264464343 | 747.4528718553156 | 38.698233090354485% |
| `10m_u_component_of_wind` | 8.641913013076056 | 9.258689192582743 | -6.661592874300112% |

### Validation Per-Lead Regressions Over 10%

| Channel | Lead days | Candidate RMSE | Incumbent RMSE | Change |
| --- | ---: | ---: | ---: | ---: |
| `mean_sea_level_pressure` | 1 | 1127.0333356764686 | 421.6152580922142 | 167.31322314477714% |
| `mean_sea_level_pressure` | 2 | 1238.1144341517042 | 753.8589654080048 | 64.23687864236116% |
| `mean_sea_level_pressure` | 3 | 1378.822396104734 | 1058.6672352861842 | 30.2413402575932% |
| `mean_sea_level_pressure` | 4 | 1530.3765066331862 | 1328.0046635088936 | 15.238790095027198% |
| `geopotential_500` | 1 | 835.9057232021993 | 264.8854188186653 | 215.5725698040185% |
| `geopotential_500` | 2 | 903.2357180319914 | 512.5079899143303 | 76.23836814387504% |
| `geopotential_500` | 3 | 1010.821780153592 | 761.9137665584163 | 32.66879068473844% |
| `geopotential_500` | 4 | 1145.8324550598543 | 996.2195829907414 | 15.01806174297051% |

## Measurement Lessons

- Primary score alone is insufficient for this candidate: it improves by `0.19845155161644534` on iteration and `0.18225098878562807` on validation, while fixed early mass-field RMSE guardrails fail.
- The candidate improves early `2m_temperature` and `10m_u_component_of_wind` RMSE, but early `geopotential_500` and `mean_sea_level_pressure` regressions are too large for the fixed gates.
- The evaluation CSV includes persistence reference rows in addition to model rows. Future scoring scripts must filter by `model_name` before comparing candidate and incumbent metrics.

## Anomalies

- Cache reuse: candidate fast artifact was reused from Implementer handoff and verified. Incumbent iteration and validation artifacts were reused from `.logbook/leaderboard.json`. Candidate iteration and validation started with `cached=0` and wrote fresh run directories.
- Resource limits: no resource failure, OOM, worker fallback, or restart observed. Both Scorer runs used `requested_workers=4`, `effective_workers=4`, `gpu_count=4`.
- Failed or restarted commands: none. The validation command exited `0`, but it was run after a Scorer parsing mistake and should have been skipped after the corrected iteration gate calculation.
- Nonfinite or unstable outputs: none reported by fixed evaluator diagnostics; candidate fast, iteration, and validation all had `failed=false`, `issues=0`.

## Recommendation To Orchestrator

Report measured gate status only. The corrected iteration gate does not promote this candidate to validation because RMSE guardrails fail; validation metrics exist as an anomalous extra measurement and should not be treated as protocol-compliant promotion evidence. Orchestrator authority is required for any accept, reject, or revision decision.

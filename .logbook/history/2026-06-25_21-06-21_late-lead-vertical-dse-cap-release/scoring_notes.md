# Scoring Notes

## Gate Status

- Fast gate: passed from the provided pre-scoring record. Command `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_latecap` exited `0`; verified artifact primary score `-0.22415855014566696`, diagnostics failed `False`, issue count `0`, records `120`.
- Iteration promotion gate: did not promote. Candidate primary `-0.2201311388680774` versus cached incumbent `-0.2197104515448394` gives delta `-0.00042068732323799485`, below the `+0.002` promotion threshold.
- Iteration diagnostics: passed. Candidate diagnostics failed `False` with issue count `0`.
- Iteration early day 1-5 mean RMSE guardrail: passed. Worst relative regression was `6.191927952562836e-07` for `geopotential_500`; threshold `0.02`.
- Iteration variable+lead RMSE guardrail: passed. Worst relative regression was `0.0015971997064777059` for `geopotential_500` at `336h`; threshold `0.1`.
- Leads through 120h: incumbent-equivalent by measurement. Max absolute relative RMSE movement was `3.412585971358586e-06` for `geopotential_500` at `24h`; max absolute RMSE delta was `0.000839364251163488` for `geopotential_500` at `24h`.
- Validation acceptance gate: not run. Validation was allowed only if iteration promoted, and this iteration did not promote.

## Commands And Status

| Command | Exit status | Notes |
| --- | ---: | --- |
| `uv run pytest` | 0 | Provided pre-scoring record: `262 passed, 2 skipped in 304.46s`; not rerun. |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_latecap` | 0 | Provided pre-scoring record; JSON/CSV artifacts verified. |
| `uv run python - <<'PY' ... registry.create_dycore_model check ... PY` | 0 | Candidate and incumbent both registered and constructed. |
| `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_latecap --workers 4` | 0 | Candidate iteration only; incumbent iteration reused from cache. |
| `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_latecap --workers 4` | not_run | Skipped because iteration did not promote. |

Two earlier scratch registry helper probes exited `1` because they used non-existent helper names (`MODEL_REGISTRY` and `create`). They changed no files and were followed by the successful `create_dycore_model` registry verification recorded above.

Exact registry verification command:

```bash
uv run python - <<'PY'
from dynamaxx.dycore import registry
for name in ['dino_hsl2_mass_dse_wtg_vdse_latecap', 'dino_hsl2_mass_dse_wtg_vdse_ramp']:
    registered = name in registry.dycore_model_names()
    print(f'{name}: registered={registered}')
    if registered:
        model = registry.create_dycore_model(name)
        print(f'{name}: constructed_name={model.name} type={type(model).__name__}')
PY
```

## Cache Reuse

- Iteration incumbent cache: reused `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json` and `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`. Checks passed: requested incumbent matched `.logbook/leaderboard.json`, protocol list included `iteration`, current HEAD `ff40def55ac707e8915c840b856a0aaa3345b046` matched leaderboard eval-code commit, artifact paths existed and were readable, primary score was finite, diagnostics were clean, and guardrail records were complete.
- Validation incumbent cache: not used for a candidate comparison because validation was skipped. The cached validation artifacts `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json` and `.csv` were present/readable and matched the leaderboard incumbent; no incumbent validation rerun was performed.
- No incumbent cache invalidation was found.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_latecap.json`
- Candidate fast CSV: `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_latecap.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_latecap.json`
- Candidate iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_latecap.csv`
- Incumbent iteration JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Incumbent iteration CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`
- Incumbent validation JSON: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json`
- Incumbent validation CSV: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`

## Guardrail Detail

Early day 1-5 mean RMSE regressions:

| Channel | Candidate mean RMSE | Incumbent mean RMSE | Relative delta | Pass |
| --- | ---: | ---: | ---: | --- |
| `10m_u_component_of_wind` | 4.2914548930400205 | 4.291454635917505 | 5.99150025092213e-08 | True |
| `2m_temperature` | 4.751334225170451 | 4.751335465357272 | -2.6101857674266855e-07 | True |
| `geopotential_500` | 592.5712775629829 | 592.5709106473444 | 6.191927952562836e-07 | True |
| `mean_sea_level_pressure` | 771.1149571703181 | 771.1150019948005 | -5.8129438928888284e-08 | True |


Worst variable+lead RMSE regression: `geopotential_500` at `336h`, candidate RMSE `1100.31821961626`, incumbent RMSE `1098.5635941661108`, relative delta `0.0015971997064777059`.

## Measurement Lessons

- The late-cap candidate leaves leads through 120h effectively incumbent-equivalent by RMSE, with only tiny numerical-scale movement before the late release window.
- The late-lead cap release did not improve the fixed iteration primary score; validation should remain skipped under the provided gate.

## Anomalies

- The long iteration run completed successfully with no diagnostics failures, no issue records, and no observed resource failure.
- The only command anomalies were the two scratch registry-helper probes described above; they did not affect source, protocol, cache, or metric artifacts.

## Recommendation To Orchestrator

Report measured status as iteration-not-promoted. Do not run validation for this candidate under the stated gate. This note measures only and does not decide acceptance or rejection.

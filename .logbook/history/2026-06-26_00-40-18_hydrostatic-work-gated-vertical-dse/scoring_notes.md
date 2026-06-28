# Scoring Notes

## Scope

- Role: Scorer.
- Proposal slug: `hydrostatic-work-gated-vertical-dse`.
- Candidate: `dino_hsl2_mass_dse_wtg_vdse_hwg`.
- Incumbent: `dino_hsl2_mass_dse_wtg_vdse_ramp`.
- History directory: `.logbook/history/2026-06-26_00-40-18_hydrostatic-work-gated-vertical-dse`.
- Worker count: `4`.
- Golden was not run.

## Commands

| Command | Status | Exit |
| --- | --- | --- |
| `uv run python -c "from dynamaxx.dycore.registry import create_dycore_model, dycore_model_names; names=('dino_hsl2_mass_dse_wtg_vdse_hwg','dino_hsl2_mass_dse_wtg_vdse_ramp'); registered=dycore_model_names(); print({name: (name in registered, type(create_dycore_model(name)).__name__) for name in names})"` | run | 0 |
| `uv run pytest` | verified from pre-scoring record | 0 |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_hwg` | verified from pre-scoring artifact | 0 |
| `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_hwg --workers 4` | run | 0 |
| `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_hwg --workers 4` | not run | n/a |

Pre-scoring pytest record: `259 passed, 2 skipped in 303.81s`.

## Registry

Both requested models are registered and construct successfully:

- `dino_hsl2_mass_dse_wtg_vdse_hwg`: `DinosaurPrimitiveEquationsDycoreModel`.
- `dino_hsl2_mass_dse_wtg_vdse_ramp`: `DinosaurPrimitiveEquationsDycoreModel`.

## Incumbent Cache

Iteration incumbent metrics were reused from the leaderboard cache:

- JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`.
- CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`.

Validation incumbent metrics were checked and available but not used because candidate validation was skipped:

- JSON: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json`.
- CSV: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`.

Cache checks performed:

- Requested incumbent matched `.logbook/leaderboard.json`: `dino_hsl2_mass_dse_wtg_vdse_ramp`.
- Leaderboard incumbent commit matched current `HEAD`: `ff40def55ac707e8915c840b856a0aaa3345b046`.
- Leaderboard artifact paths matched the provided cached artifacts.
- Cached iteration and validation primary scores were finite.
- Cached artifacts contained 60 incumbent model rows each, covering 4 target variables and leads 1..15 days.
- Leaderboard fingerprint included `iteration` and `validation`, target variables matched, and lead range was `1..15`.
- Dirty files were candidate dycore/test changes only; fixed evaluation protocol files were not modified.
- Candidate source edits were not treated as cache invalidation under `roles/PROTOCOL.md` and `roles/SCORER.md`.

## Fast

- Candidate primary score: `-0.34772607973591296`.
- Diagnostics failed: `false`.
- Issue count: `0`.
- Records: `120` total, `60` candidate model rows.
- Artifacts: `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_hwg.json`, `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_hwg.csv`.

Anomaly: the fast primary score was substantially lower than the cached incumbent-family iteration level despite clean diagnostics and zero issues.

## Iteration

- Candidate primary score: `-0.34541538912978986`.
- Incumbent primary score: `-0.2197104515448394`.
- Signed primary delta, candidate minus incumbent: `-0.12570493758495047`.
- Absolute primary delta: `0.12570493758495047`.
- Primary threshold checked: `+0.002`.
- Primary threshold pass: `false`.
- Candidate diagnostics failed: `false`; issue count: `0`.
- Incumbent diagnostics failed: `false`; issue count: `0`.
- Candidate artifacts: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_hwg.json`, `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_hwg.csv`.

Early day-1-to-5 mean RMSE guardrail, threshold `2%` regression:

| Variable | Candidate mean RMSE | Incumbent mean RMSE | Regression | Pass |
| --- | ---: | ---: | ---: | --- |
| `10m_u_component_of_wind` | `4.419796108354167` | `4.291454635917505` | `2.9906286638218926%` | false |
| `2m_temperature` | `5.27300260058162` | `4.751335465357272` | `10.979379145671885%` | false |
| `geopotential_500` | `606.2891669505964` | `592.5709106473444` | `2.315040454528172%` | false |
| `mean_sea_level_pressure` | `788.3156536845194` | `771.1150019948005` | `2.230620808209194%` | false |

Worst variable+lead RMSE guardrail, threshold `10%` regression:

- Pass: `false`.
- Failing variable+lead count over the 60 model rows: `30`.
- Worst case: `2m_temperature`, lead `144` hours (`6.0` days), candidate RMSE `7.995312795655586`, incumbent RMSE `6.712419167708991`, regression `19.11223950551435%`.

Largest observed variable+lead regressions:

| Variable | Lead hours | Candidate RMSE | Incumbent RMSE | Regression |
| --- | ---: | ---: | ---: | ---: |
| `2m_temperature` | `144` | `7.995312795655586` | `6.712419167708991` | `19.11223950551435%` |
| `2m_temperature` | `120` | `7.504162355718708` | `6.324612420445005` | `18.650153667293168%` |
| `2m_temperature` | `168` | `8.28573143714878` | `6.992728022319562` | `18.490686477468856%` |
| `2m_temperature` | `192` | `8.46425358284868` | `7.205919663928306` | `17.462502742285558%` |
| `2m_temperature` | `216` | `8.556265759995048` | `7.36316176431721` | `16.203691211291414%` |

## Validation

Candidate validation was not run. The iteration primary delta was below `+0.002`, and the iteration RMSE guardrails did not pass.

Cached incumbent validation metrics remain available for future protocol use:

- Incumbent validation primary score: `-0.21940899263836755`.
- Diagnostics failed: `false`.
- Issue count: `0`.
- Records: `120` total, `60` incumbent model rows.

## Measurement Lessons

- The hydrostatic-work gate produced clean diagnostics but degraded the primary score materially on iteration.
- The largest RMSE regressions are concentrated in `2m_temperature`, especially days 5-9.
- The fast-score anomaly was directionally consistent with the iteration result: both candidate primary scores were strongly below the cached incumbent level.

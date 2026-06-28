# Scoring Notes

## Gate Status

- Fast artifact verification: passed. Reused `outputs/eval/fast_dino_hsl2_mass_dse_pressure_tide.json`; top-level model matched `dino_hsl2_mass_dse_pressure_tide`, `failed=False`, `issues=0`, `records=120`, primary score `-0.28549097969436926`.
- Iteration promotion gate: failed. Candidate primary score was `-0.2857361476786912`; cached incumbent primary score was `-0.2616483974683927`; signed delta was `-0.02408775021029852`, below the `+0.002` promotion threshold.
- Candidate iteration diagnostics were clean: `failed=False`, `issues=0`.
- Early lead days 1-5 mean RMSE guardrail: failed. Worst early regression was `geopotential_500` with `12.830770258222913` percent relative regression.
- Individual variable/lead RMSE guardrail: failed. Worst regression was `geopotential_500` at lead day `1` with `16.94183102106469` percent relative regression.
- Validation: not run, because iteration promotion thresholds did not pass. Golden was not run.

## Commands And Status

- Verified Orchestrator full pytest record, not rerun by Scorer: `uv run pytest` exit 0, `247 passed`, `2 skipped`, `223.11s`.
- Confirmed model registration with `uv run python - <<'PY' ... create_dycore_model(...) ... PY`: exit 0 for `dino_hsl2_mass_dse_pressure_tide` and `dino_hsl2_mass_dse`.
- Verified reusable fast artifact with `python - <<'PY' ... verify outputs/eval/fast_dino_hsl2_mass_dse_pressure_tide.json ... PY`: exit 0.
- Validated incumbent iteration and validation caches with `python - <<'PY' ... validate leaderboard incumbent iteration and validation caches ... PY`: exit 0.
- Checked data path with `test -d /home/ubuntu/data/weathermaxx-data/weatherbench2/datasets/v1/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative && echo data_path_exists=true`: exit 0.
- Checked fixed eval code worktree diff with `git diff --name-only -- src/dynamaxx/eval tests/eval pyproject.toml uv.lock`: exit 0, no output.
- Ran `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_pressure_tide --workers 4`: exit 0, `failed=False`, `issues=0`, `records=120`, primary score `-0.2857361476786912`.
- Computed guardrails with `python - <<'PY' ... compute primary delta and RMSE guardrails ... PY`: exit 0.
- Did not run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_pressure_tide --workers 4` because iteration failed promotion gates.
- Did not run golden; golden is prohibited for this iteration.

## Cache Reuse

- Iteration incumbent metrics were reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dino_hsl2_mass_dse.json` and `outputs/eval/iteration_dino_hsl2_mass_dse.csv`.
- Validation incumbent metrics were checked and valid but not used for candidate comparison because validation was not run: `outputs/eval/validation_dino_hsl2_mass_dse.json` and `outputs/eval/validation_dino_hsl2_mass_dse.csv`.
- Cache validation checks: requested incumbent matched the leaderboard incumbent; `HEAD` matched leaderboard `eval_code_commit` `2c70bb5b77370a074330c2b46954f74f20771f12`; fixed data path, target variables, lead range, and protocols matched; artifacts were readable; primary scores were finite; exact incumbent rows covered the four target variables at lead hours 24 through 360; incumbent diagnostics were clean.
- Candidate source, side-by-side registry additions, and tests did not invalidate the accepted incumbent cache under `roles/SCORER.md`.

## Guardrail Details

- Iteration early mean RMSE relative regressions over days 1-5:
  - `2m_temperature`: `0.11976371138230346` percent; passed `True`.
  - `mean_sea_level_pressure`: `8.481852632772549` percent; passed `False`.
  - `geopotential_500`: `12.830770258222913` percent; passed `False`.
  - `10m_u_component_of_wind`: `0.7267934713195381` percent; passed `True`.
- Iteration worst variable/lead RMSE regressions by variable:
  - `2m_temperature`: lead day `3`, `0.18157456049835952` percent; passed `True`.
  - `mean_sea_level_pressure`: lead day `3`, `10.0117132850309` percent; passed `False`.
  - `geopotential_500`: lead day `1`, `16.94183102106469` percent; passed `False`.
  - `10m_u_component_of_wind`: lead day `4`, `0.9022805962761331` percent; passed `True`.

## Artifacts

- Candidate fast: `outputs/eval/fast_dino_hsl2_mass_dse_pressure_tide.json`, `outputs/eval/fast_dino_hsl2_mass_dse_pressure_tide.csv`.
- Candidate iteration: `outputs/eval/iteration_dino_hsl2_mass_dse_pressure_tide.json`, `outputs/eval/iteration_dino_hsl2_mass_dse_pressure_tide.csv`.
- Candidate validation: not run; no candidate validation artifact expected.
- Incumbent iteration cache: `outputs/eval/iteration_dino_hsl2_mass_dse.json`, `outputs/eval/iteration_dino_hsl2_mass_dse.csv`.
- Incumbent validation cache: `outputs/eval/validation_dino_hsl2_mass_dse.json`, `outputs/eval/validation_dino_hsl2_mass_dse.csv`.
- Score artifacts written here: `.logbook/history/2026-06-24_18-53-21_migrating-pressure-tide-forcing/scores.json` and `.logbook/history/2026-06-24_18-53-21_migrating-pressure-tide-forcing/scoring_notes.md`.

## Measurement Lessons

- The pressure-tide candidate was numerically clean but materially worse on the fixed iteration primary score.
- The strongest degradation was early `geopotential_500`, including `16.94183102106469` percent day-1 RMSE regression and `12.830770258222913` percent day-1-to-5 mean RMSE regression.
- Mean sea-level pressure also failed guardrails, consistent with the candidate directly perturbing surface pressure.
- Fast diagnostics remained clean, but iteration exposed large skill and guardrail regressions, so fast should stay a sanity gate only.
- Metric artifacts include both exact model rows and persistence rows; all comparisons used exact `model_name` filters.

## Anomalies

- The candidate iteration run had a long supervised runtime and sparse chunk output in places, but it made steady progress and exited 0.
- No resource failure, nonfinite output, diagnostic issue, restarted command, incumbent rerun, validation run, or golden run occurred.

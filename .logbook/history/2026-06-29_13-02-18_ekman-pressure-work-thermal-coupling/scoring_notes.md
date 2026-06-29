# Scoring Notes: ekman-pressure-work-thermal-coupling

## Scope

Scored exactly one implemented candidate, `dino_ri2m_ekman_pwork`, against incumbent `dino_ri2m_ekman_coupled`. No dycore source, tests, fixed evaluation code, metric definitions, target variables, splits, leaderboard, commits, or golden protocol were changed or run.

## Commands And Outputs

- `uv run pytest`: exit 0; 280 passed, 2 skipped in 289.91s.
- `uv run dynamaxx-eval fast --model dino_ri2m_ekman_pwork`: exit 0; failed=False, issues=0, primary_score=-0.16684765062987625; artifacts `outputs/eval/fast_dino_ri2m_ekman_pwork.json` and `outputs/eval/fast_dino_ri2m_ekman_pwork.csv`.
- `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_pwork --workers 4`: exit 0; failed=False, issues=0, primary_score=-0.16408904344830819; artifacts `outputs/eval/iteration_dino_ri2m_ekman_pwork.json` and `outputs/eval/iteration_dino_ri2m_ekman_pwork.csv`.
- Validation was not run because the iteration promotion gate failed.
- Golden was not run.

## Incumbent Cache Reuse

Incumbent iteration metrics were reused from `outputs/eval/iteration_dino_ri2m_ekman_coupled.json` and `outputs/eval/iteration_dino_ri2m_ekman_coupled.csv`. No incumbent rerun occurred.

Cache validation checks performed:

- Requested incumbent matched `.logbook/leaderboard.json`: `dino_ri2m_ekman_coupled`.
- Leaderboard fingerprint protocol list includes `iteration` and `validation`.
- Fixed CLI uses `WEATHERBENCH2_ERA5_1P5DEG_6H_PATH`, matching leaderboard data path `/home/ubuntu/data/weathermaxx-data/weatherbench2/datasets/v1/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative`.
- Target variables match: 2m_temperature, mean_sea_level_pressure, geopotential_500, 10m_u_component_of_wind.
- Lead range matches: 1..15 days.
- `git diff --name-only d187308d30a242bf38aabe5b7eb530fca522a68f -- src/dynamaxx/eval src/dynamaxx/cli.py src/dynamaxx/data tests/eval pyproject.toml uv.lock` returned no changed files, so fixed eval code/dependencies are compatible with the cached incumbent commit.
- Cached incumbent iteration artifact is readable, has model `dino_ri2m_ekman_coupled`, finite primary score -0.16500618979404214, 60 incumbent target rows, finite RMSE rows, failed=False, issues=0.
- Cached incumbent validation artifact was also readable and compatible, but candidate validation was skipped so it was not used for a candidate validation comparison.
- Candidate source edits do not invalidate the accepted incumbent cache under `roles/PROTOCOL.md` and `roles/SCORER.md`.

## Gate Calculations

Iteration primary delta: -0.16408904344830819 - -0.16500618979404214 = 0.000917146345733949.

Iteration promotion requires delta >= +0.002. This candidate did not pass that primary-score threshold.

Guardrails were clean:

- Largest early-lead mean RMSE regression: geopotential_500 = 0.014313359049992355% over leads 1-5 days, below 2%.
- Largest single-lead RMSE regression: geopotential_500 at 192h = 0.021754943631316342%, below 10%.
- Candidate diagnostics were clean for fast and iteration: failed=False, issues=0.

## Measurement Lesson

The pressure-work thermal response is stable and guardrail-clean, but its iteration primary improvement is only +0.000917146345733949, below the promotion threshold. Future variants should not spend validation compute on this candidate state unless the Orchestrator requests a bounded revision that first clears a new iteration gate.

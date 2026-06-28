# Scoring Notes

## Gate Status

- Fast gate: passed. Existing candidate fast artifact was compatible and diagnostics were clean (`failed=False`, issues `0`). Fast primary was `-1.514762612813002`; fast primary was not used as the promotion gate.
- Iteration promotion gate: did not pass. Candidate primary `-1.55975435053939` vs incumbent `-1.215522043834977` gives delta `-0.3442323067044137`, below the required `+0.002`. Candidate iteration diagnostics were clean (`failed=False`, issues `0`).
- Early mean RMSE guardrail over day 1-5 leads: did not pass; `2` variables exceeded the 2% regression limit.
- Variable+lead RMSE guardrail: did not pass; `30` variable/lead rows exceeded the 10% regression limit. Maximum relative regression was `56.297419%` for `geopotential_500` at lead `360h`.
- Validation acceptance gate: not evaluated. Validation was allowed, but the candidate did not pass the iteration promotion gate, so the required validation command was not run.

## Command Details

- `uv run pytest`: exit `0`; `115 passed, 2 skipped in 60.36s`.
- Fast verification command: exit `0`; checked `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_helmholtz_wind.json` for candidate model, fast case, 24-360h leads, four target channels, 120 records, and clean diagnostics.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_helmholtz_wind --workers 4`: exit `0`; command reported `cached=0 pending=229`, merged 229 chunks, wrote `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_logp_init_helmholtz_wind.json` and `.csv`, with `failed=False`, issues `0`, records `120`, primary `-1.55975435053939`.
- `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_helmholtz_wind --workers 4`: not run because iteration promotion failed.

## RMSE Guardrails

Early mean RMSE day 1-5 by variable:

- 10m_u_component_of_wind: candidate mean RMSE 9.40758980184, incumbent 9.25251060824, relative delta 1.676077% (pass)
- 2m_temperature: candidate mean RMSE 7.38843727349, incumbent 7.39177877157, relative delta -0.045206% (pass)
- geopotential_500: candidate mean RMSE 936.687054327, incumbent 770.253372937, relative delta 21.607654% (FAIL)
- mean_sea_level_pressure: candidate mean RMSE 1272.18428876, incumbent 1047.51527412, relative delta 21.447803% (FAIL)

Top variable+lead RMSE regressions over the 10% guardrail:

- geopotential_500 lead 360h: candidate RMSE 3533.43851501, incumbent 2260.71456514, relative delta 56.297419%
- mean_sea_level_pressure lead 360h: candidate RMSE 4579.87445506, incumbent 2939.47363052, relative delta 55.805938%
- geopotential_500 lead 336h: candidate RMSE 3365.41145944, incumbent 2217.62355289, relative delta 51.757563%
- mean_sea_level_pressure lead 336h: candidate RMSE 4366.1033444, incumbent 2882.87184952, relative delta 51.449789%
- geopotential_500 lead 312h: candidate RMSE 3191.05356288, incumbent 2164.0690943, relative delta 47.456177%
- mean_sea_level_pressure lead 312h: candidate RMSE 4143.43244907, incumbent 2811.88796325, relative delta 47.354109%
- geopotential_500 lead 288h: candidate RMSE 3010.25247819, incumbent 2089.1683781, relative delta 44.088553%
- mean_sea_level_pressure lead 288h: candidate RMSE 3907.93899287, incumbent 2713.30777283, relative delta 44.028592%
- mean_sea_level_pressure lead 264h: candidate RMSE 3667.7330966, incumbent 2605.04866113, relative delta 40.793266%
- geopotential_500 lead 264h: candidate RMSE 2827.83298945, incumbent 2010.15790468, relative delta 40.677157%

Full per-variable and per-lead calculations are recorded in `scores.json`.

## Measurement Lessons

- The Helmholtz wind initialization produced clean finite outputs under fast and iteration protocols, but it materially worsened iteration primary skill and pressure/geopotential RMSE against the incumbent.
- The largest regressions are concentrated in `geopotential_500` and `mean_sea_level_pressure`, growing with lead time; future wind-initialization proposals should specifically protect mass/geopotential balance and long-lead pressure drift.
- The 10 m wind early mean RMSE increased by `1.676077%`, which stayed within the 2% early-mean guardrail, but that local wind behavior did not translate into primary-score improvement.

## Anomalies

- Cache reuse: candidate fast artifact reused after compatibility verification; incumbent iteration artifact reused; candidate iteration was fresh with no cached chunks.
- Resource limits: no resource failure observed. Pre-run resources were 48 CPUs, about 174 GiB available RAM, and about 4.1 TiB free disk. During iteration, GPU dispatch used 4 GPUs with about 17.4 GiB used per GPU and 100% utilization when sampled.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by official diagnostics.
- Worktree note: source tree was already dirty before scoring, containing candidate implementation/test changes. Scoring did not modify source files.

## Recommendation To Orchestrator

Report the measured gate status and caveats above. This Scorer report does not accept or reject the candidate.

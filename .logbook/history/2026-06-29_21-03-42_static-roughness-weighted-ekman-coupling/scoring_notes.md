# Scoring Notes: static-roughness-weighted-ekman-coupling

## Scope

Scored exactly one candidate model, `dino_ri2m_ekman_z0`, against incumbent `dino_ri2m_ekman_coupled`. I did not change dycore source, tests, fixed evaluation code, metrics, target variables, splits, lead ranges, the leaderboard, or commits. Golden was not run.

## Commands And Outcomes

- `uv run pytest`: exit 0, `283 passed, 2 skipped in 286.93s`.
- `uv run dynamaxx-eval fast --model dino_ri2m_ekman_z0`: exit 0, `failed=False`, `issues=0`, `records=120`, primary score `-0.16771985596313563`.
- `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_z0 --workers 4`: exit 0, `failed=False`, `issues=0`, `records=120`, primary score `-0.16500609426017815`.
- `uv run python` registration check with `create_dycore_model()` and `dycore_model_names()`: exit 0; both candidate and incumbent are registered and creatable.
- `git diff --name-only d187308d30a242bf38aabe5b7eb530fca522a68f -- src/dynamaxx/eval tests/eval pyproject.toml uv.lock`: exit 0 with no output.
- `git diff --name-only -- src/dynamaxx/eval tests/eval pyproject.toml uv.lock roles/PROTOCOL.md roles/SCORER.md`: exit 0 with no output.

## Cache Validation

Incumbent metrics were reused from `.logbook/leaderboard.json`; no incumbent rerun occurred.

Iteration cache checks passed:

- requested incumbent matched leaderboard incumbent `dino_ri2m_ekman_coupled`;
- `outputs/eval/iteration_dino_ri2m_ekman_coupled.json` and `outputs/eval/iteration_dino_ri2m_ekman_coupled.csv` existed and were readable;
- cached incumbent iteration primary score `-0.16500618979404214` was finite;
- cached artifact contained 60 evaluated-model rows for `dino_ri2m_ekman_coupled` and the candidate artifact contained matching variable/lead guardrail rows;
- fingerprint protocol included `iteration`;
- target variables matched the leaderboard fingerprint: `['2m_temperature', 'mean_sea_level_pressure', 'geopotential_500', '10m_u_component_of_wind']`;
- lead days matched `1..15` with 24h through 360h rows;
- fixed eval code/dependency paths had no diff from incumbent commit `d187308d30a242bf38aabe5b7eb530fca522a68f`;
- current candidate source edits did not touch fixed eval code or policy files and do not invalidate the accepted incumbent cache under `roles/PROTOCOL.md` and `roles/SCORER.md`.

Validation cache was readable and finite, but validation was not run or used for candidate comparison because the iteration promotion gate failed.

Metric guardrails were computed only from rows whose `model_name` matched the evaluated model. The raw artifacts also include persistence baseline rows, so unfiltered variable/lead maps would be incorrect.

## Score Comparison

Iteration primary score:

- candidate: `-0.16500609426017815`
- cached incumbent: `-0.16500618979404214`
- delta: `9.553386398630792e-08`
- required delta for validation promotion: `+0.002`

The iteration primary gate failed because `9.553386398630792e-08` is below `+0.002`.

## Guardrails

Diagnostics were clean: fast candidate failed `False`, iteration candidate failed `False`, both with zero issues.

Largest early-lead mean RMSE regression over leads 1-5 days was `1.9102354370693865e-05` percent for `10m_u_component_of_wind`, below the 2 percent guardrail.

Largest single-lead RMSE regression was `0.0001657404768912333` percent for `geopotential_500` at lead `24` hours, below the 10 percent guardrail.

## Gate Status

The candidate passed unit tests, fast diagnostics, iteration diagnostics, and RMSE guardrails. It failed iteration promotion only on primary score delta. Validation was skipped per protocol. Golden was not run.

## Measurement Lessons

The static roughness redistribution was numerically stable and essentially neutral against the accepted coupled Ekman incumbent. Its iteration primary gain was only `9.553386398630792e-08`, several orders of magnitude below the promotion threshold. Future roughness ideas need a stronger dynamical signal than bounded land/sea/coast redistribution of the accepted coupling, or should be staged until a better static roughness proxy is available.

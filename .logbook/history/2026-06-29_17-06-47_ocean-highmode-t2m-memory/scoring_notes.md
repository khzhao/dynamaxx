# Scoring Notes: ocean-highmode-t2m-memory

## Scope

Scored exactly one candidate model, `dino_ri2m_ekman_ocean_t2m_himem`, against incumbent `dino_ri2m_ekman_coupled`. I did not change dycore source, tests, fixed evaluation code, metrics, target variables, splits, lead ranges, the leaderboard, or commits. Golden was not run.

## Commands And Outcomes

- `uv run pytest`: exit 0, `281 passed, 2 skipped in 291.63s`.
- `uv run dynamaxx-eval fast --model dino_ri2m_ekman_ocean_t2m_himem`: exit 0, `failed=False`, `issues=0`, `records=120`, primary score `-0.16799146437056978`.
- `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_ocean_t2m_himem --workers 4`: exit 0, `failed=False`, `issues=0`, `records=120`, primary score `-0.16534409792665697`.
- Two initial registration probes used non-existent registry helper names and exited 1; these were API-discovery mistakes, not evaluation failures. The corrected check with `create_dycore_model()` and `dycore_model_names()` exited 0 and confirmed both candidate and incumbent are registered and creatable.
- `git diff --name-only d187308d30a242bf38aabe5b7eb530fca522a68f -- src/dynamaxx/eval tests/eval pyproject.toml uv.lock`: exit 0 with no output.
- `git diff --name-only -- src/dynamaxx/eval tests/eval pyproject.toml uv.lock roles/PROTOCOL.md roles/SCORER.md`: exit 0 with no output.

## Cache Validation

Incumbent metrics were reused from `.logbook/leaderboard.json`; no incumbent rerun occurred.

Iteration cache checks passed:

- requested incumbent matched leaderboard incumbent `dino_ri2m_ekman_coupled`;
- `outputs/eval/iteration_dino_ri2m_ekman_coupled.json` and `.csv` existed and were readable;
- cached incumbent iteration primary score `-0.16500618979404214` was finite;
- cached artifact contained 60 rows for `dino_ri2m_ekman_coupled` and the candidate artifact contained matching variable/lead guardrail rows;
- fingerprint protocol included `iteration`;
- candidate target variables `['2m_temperature', 'mean_sea_level_pressure', 'geopotential_500', '10m_u_component_of_wind']` matched the leaderboard fingerprint;
- candidate lead days `1..15` matched the leaderboard fingerprint;
- fixed eval code/dependency paths had no diff from incumbent commit `d187308d30a242bf38aabe5b7eb530fca522a68f`;
- current candidate source edits did not touch fixed eval code or policy files and do not invalidate the accepted incumbent cache under `roles/PROTOCOL.md` and `roles/SCORER.md`.

Validation cache was readable and finite, but validation was not run or used for candidate comparison because the iteration promotion gate failed.

## Score Comparison

Iteration primary score:

- candidate: `-0.16534409792665697`
- cached incumbent: `-0.16500618979404214`
- delta: `-0.00033790813261483366`
- required delta for validation promotion: `+0.002`

The iteration primary gate failed because `-0.00033790813261483366` is below `+0.002`.

## Guardrails

Diagnostics were clean: fast candidate failed `False`, iteration candidate failed `False`, both with zero issues.

Largest early-lead mean RMSE regression over leads 1-5 days was `0.04663942027907426` percent for `2m_temperature`, below the 2 percent guardrail.

Largest single-lead RMSE regression was `0.14264303350307025` percent for `2m_temperature` at lead `144` hours, below the 10 percent guardrail.

## Gate Status

The candidate passed unit tests, fast diagnostics, iteration diagnostics, and RMSE guardrails. It failed iteration promotion only on primary score delta. Validation was skipped per protocol. Golden was not run.

## Measurement Lessons

The ocean high-mode T2m memory mechanism was numerically stable and guardrail-clean, but it slightly worsened the fixed iteration primary score relative to the cached accepted incumbent. The next proposal should avoid narrow T2m-only high-mode memory unless it has a stronger mechanism for improving the broad primary score, not just keeping guardrails quiet.

# Scoring Notes

## Gate Status

- Fast gate: passed from reused artifact `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_seasonal.json`; exact candidate records 60 of 120, primary score `-1.2291930627718617`, diagnostics `failed=false`, issue count `0`.
- Iteration promotion gate: did not pass. Candidate iteration primary score was `-1.2621122452124416`; incumbent iteration primary score was `-1.2218408656785489`; delta was `-0.040271379533892704` versus the required `+0.002`.
- Iteration diagnostics: passed. Candidate iteration diagnostics were `failed=false` with `0` issues.
- Iteration early RMSE guardrail: did not pass. `2m_temperature` day 1-5 mean RMSE changed from `7.401365301163406` to `7.604999420719304`, a `0.02751304810261005` relative regression, exceeding the `0.02` threshold.
- Iteration variable-lead RMSE guardrail: did not pass. `2m_temperature` exceeded the `0.10` threshold at lead hours `312`, `336`, and `360`; the maximum was lead hour `360`, from `10.438223540412169` to `11.784680160133394`, a `0.12899288988287547` relative regression.
- Validation acceptance gate: not run. Protocol allows validation only after iteration promotion, and the iteration gate failed.

## Commands And Artifacts

- `uv run python - <<'PY' ... registration check ... PY` -> exit `0`; confirmed `dinosaur_dfi_surface_residual_weak_hs_seasonal` and `dinosaur_dfi_surface_residual_weak_hs` are registered and instantiate with exact expected names.
- `uv run pytest` -> exit `0`; `110 passed, 2 skipped in 58.92s`.
- Reused Implementer fast command artifact from `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_seasonal` -> recorded exit `0`; raw paths `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_seasonal.json` and `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_seasonal.csv`.
- `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_seasonal --workers 4` -> exit `0`; raw paths `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_seasonal.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_seasonal.csv`.
- Reused incumbent iteration artifacts `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs.json` and `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs.csv`; exact incumbent records 60 of 120, primary score `-1.2218408656785489`, diagnostics clean.
- Reused incumbent validation artifacts `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs.json` and `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs.csv`; exact incumbent records 60 of 120, primary score `-1.2103467803549615`, diagnostics clean. Candidate validation was not run.

## Measurement Lessons

- The candidate was finite and diagnostic-clean but materially worse on the fixed iteration primary score.
- The regression was concentrated in `2m_temperature`, with both early lead and long lead guardrail failures.
- Future seasonal or Held-Suarez-family forcing proposals should include a cheap pre-iteration check for 2 m temperature drift because the fast diagnostic gate stayed clean here.

## Anomalies

- Cache reuse: candidate fast was reused after exact-model verification; incumbent iteration and validation were reused from leaderboard-compatible artifacts. Candidate iteration was a fresh run with `cached=0`, `pending=229`.
- Resource limits: none observed. Candidate iteration used GPU dispatch with requested workers `4`, effective workers `4`, and worker devices `0:0,1:1,2:2,3:3`.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by diagnostics.

## Recommendation To Orchestrator

Report the measured gate status only: fast passed, iteration did not promote to validation, and validation was not run. Acceptance or rejection remains with the Orchestrator.

# Scoring Notes

Candidate model: `dinosaur_dfi_surface_residual_weak_hs_dry_dfi`

Incumbent model: `dinosaur_dfi_surface_residual_weak_hs`

Generated at: `2026-06-16T23:29:20Z`

Repository commit: `4756cc9a4b69c41eec60e2177fb03a73974f0e2d` with uncommitted Implementer changes present.

## Command Record

- Required inputs were read: `roles/PROTOCOL.md`, `roles/SCORER.md`, the history `proposal.md`, the history `implementation.md`, `.logbook/leaderboard.json`, `roles/templates/scores.json`, and `roles/templates/scoring_notes.md`; read-only commands exited 0.
- Worktree inspection: `git status --short` exited 0 and showed only Implementer-owned dycore/test changes before scoring artifacts were written.
- Initial registry probe: `uv run python -c "from dynamaxx.dycore.registry import list_dycore_models, create_dycore_model; ..."` exited 1 because the registry helper is named `dycore_model_names`, not `list_dycore_models`; no files were changed.
- Corrected registry check: `uv run python -c "from dynamaxx.dycore.registry import dycore_model_names, create_dycore_model; ..."` exited 0 and confirmed both exact model names are registered and instantiable.
- Full tests: `uv run pytest` exited 0 with `108 passed, 2 skipped in 50.83s`.
- Fast gate reuse check: `jq '{model_name, primary_score, failed:.diagnostics.failed, issue_count:(.diagnostics.issues|length), total_records:(.records|length), filtered_candidate_records:([.records[] | select(.model_name == "dinosaur_dfi_surface_residual_weak_hs_dry_dfi")] | length), filtered_persistence_records:([.records[] | select(.model_name == "persistence")] | length)}' outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_dry_dfi.json` exited 0.
- Candidate iteration: `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_dry_dfi --workers 4` exited 0. It started at `2026-06-16T22:43:56Z`, finished at `2026-06-16T23:28:27Z`, reported `chunks=229 cached=0 pending=229`, and wrote the raw iteration JSON/CSV.
- Iteration comparison: `uv run python - <<'PY' ... PY` exited 0 after exact `model_name` filtering and fixed guardrail calculations.
- Validation was not run because the iteration promotion gate failed. `golden` was not run.

## Raw Artifacts

- Candidate fast JSON: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_dry_dfi.json`
- Candidate fast CSV: `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_dry_dfi.csv`
- Candidate iteration JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_dry_dfi.json`
- Candidate iteration CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs_dry_dfi.csv`
- Incumbent iteration JSON reused: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs.json`
- Incumbent iteration CSV reused: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs.csv`
- Incumbent validation JSON available but not used for a candidate comparison: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs.json`
- Incumbent validation CSV available but not used for a candidate comparison: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs.csv`

## Gate Status

- Fast gate: passed by reusing the Implementer artifact after verification. Candidate primary `-1.1909671157650277`; diagnostics `failed=false`; issue count `0`; exact candidate records `60`; persistence records `60`.
- Iteration promotion gate: failed. Candidate primary `-1.2218391186283701`; incumbent primary `-1.2218408656785489`; primary delta `+0.0000017470501787464343`, below the required `+0.002`. Diagnostics were clean and both RMSE guardrails passed.
- Validation acceptance gate: not run. The protocol allows validation only if the iteration promotion gate passes.

## Iteration Guardrails

Early mean RMSE regressions, leads day 1-5:

| Channel | Candidate mean RMSE | Incumbent mean RMSE | Relative regression | Guardrail |
| --- | ---: | ---: | ---: | --- |
| `10m_u_component_of_wind` | 9.256871669553973 | 9.25692289266928 | -0.000005533492706011654 | pass |
| `2m_temperature` | 7.40135558913273 | 7.401365301163406 | -0.000001312194477827062 | pass |
| `geopotential_500` | 771.9964754560266 | 771.9761195101368 | 0.000026368621224643066 | pass |
| `mean_sea_level_pressure` | 1050.7353429741893 | 1050.7180420326392 | 0.00001646582704202763 | pass |

Max variable+lead RMSE regressions:

| Channel | Lead hours | Candidate RMSE | Incumbent RMSE | Relative regression | Guardrail |
| --- | ---: | ---: | ---: | ---: | --- |
| `10m_u_component_of_wind` | 264 | 15.048982393587913 | 15.048906526578008 | 0.000005041363621376409 | pass |
| `2m_temperature` | 336 | 10.55923984128224 | 10.559203154291739 | 0.0000034744090027864345 | pass |
| `geopotential_500` | 48 | 525.9144991461093 | 525.880373504403 | 0.00006489240410109463 | pass |
| `mean_sea_level_pressure` | 72 | 1080.4617048367975 | 1080.4099051994165 | 0.000047944430286807047 | pass |

Global max variable+lead regression: `geopotential_500` at `48` hours, relative regression `0.00006489240410109463`.

## Measurement Lessons

- Evaluation JSON files include persistence rows; all scoring comparisons filtered by exact `model_name` before computing record counts, primary score checks, and RMSE guardrails.
- The candidate is numerically very close to the incumbent on the fixed iteration protocol. The measured primary movement was positive but roughly three orders of magnitude below the promotion threshold.
- The measured failure mode is effect size only: diagnostics were clean, all early mean RMSE guardrails passed, and all variable+lead RMSE guardrails passed.
- Because the iteration gate failed, validation was intentionally not run; there is no candidate validation artifact for this iteration.

## Anomalies

- Cache reuse: candidate fast was reused from the Implementer run after verification; incumbent iteration and validation artifacts were reused from the leaderboard; candidate iteration was fresh with `cached=0`.
- Resource limits: none observed. Candidate iteration used four GPU workers; a mid-run `nvidia-smi` snapshot showed all four GPUs at 100% utilization with about 17.4 GiB used and about 5.2 GiB free on each.
- Failed or restarted commands: one read-only registry probe failed because it used the wrong helper name; the corrected registry command exited 0. No evaluation command failed or restarted.
- Nonfinite or unstable outputs: none. Candidate fast and iteration diagnostics reported `failed=false` and zero issues.

## Recommendation To Orchestrator

Report the measured gate status only. The iteration promotion gate did not pass, so validation was not run.

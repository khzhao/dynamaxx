# Scoring Notes

## Gate Status

- Fast gate: passed from the Implementer-provided artifact. Exact filtering found 60 `dinosaur_dfi_surface_residual_weak_hs_pressure_anchor` records and 60 persistence records; diagnostics were clean and primary score was `-1.1909823513604236`.
- Iteration promotion gate: failed on primary score. Candidate primary was `-1.2218418099192239`; incumbent primary was `-1.2218408656785489`; delta was `-9.44240674982666e-7`, below the required `+0.002`.
- Iteration diagnostics and RMSE guardrails: passed. Diagnostics were clean, all early day 1-5 mean RMSE regressions were below 2%, and the worst variable-lead RMSE regression was `3.262918195273341e-6`, below 10%.
- Validation acceptance gate: not run. The protocol only permits validation after the iteration promotion gate passes.

## Command Record

- Reused Implementer test record: `compileall`, changed-file `ruff format`, changed-file `ruff check`, focused pytest (`42 passed`), full pytest (`108 passed, 2 skipped`), fast eval, and `git diff --check` all exited 0.
- Confirmed registration through `create_dycore_model` for both `dinosaur_dfi_surface_residual_weak_hs_pressure_anchor` and `dinosaur_dfi_surface_residual_weak_hs`; exit 0.
- Verified the cached fast artifact with exact model-name filtering because the JSON includes persistence rows; exit 0.
- Ran `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_pressure_anchor --workers 4`; exit 0.
- Skipped `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_pressure_anchor --workers 4` because iteration did not promote.

## Measurement Lessons

- The global pressure-mode anchor produced only floating-point-scale metric movement relative to the weak-Held-Suarez incumbent, and the movement was slightly negative in aggregate.
- The clean guardrails indicate the candidate is numerically benign under the fixed iteration split, but its effect is too small to justify validation.
- Future pressure or mass-conservation ideas need a stronger mechanism than anchoring only the zero-wavenumber `log_surface_pressure` coefficient, while still avoiding spatial pressure-gradient imbalance and output-time residual tuning.

## Anomalies

- Cache reuse: incumbent iteration and validation artifacts were reused from the leaderboard inputs. Candidate fast was reused from the Implementer record. Candidate iteration was fresh: 229 chunks, 0 cached.
- Resource limits: no resource limit encountered. The scorer resource check reported 48 CPUs, 175 GiB available RAM, and 4.1 TiB free disk.
- Failed or restarted commands: one preliminary non-mutating registry check attempted to import a nonexistent `get_model` helper and exited 1 before scoring. The scorer read the registry API and reran the check through `create_dycore_model`; no evaluation, source, proposal, leaderboard, or protocol file was changed.
- Nonfinite or unstable outputs: none reported by fast or iteration diagnostics.

## Recommendation To Orchestrator

Report the measured gate status to the Orchestrator. This scorer does not accept or reject the candidate, but the measured iteration primary delta does not satisfy the protocol promotion threshold, so validation was not run.

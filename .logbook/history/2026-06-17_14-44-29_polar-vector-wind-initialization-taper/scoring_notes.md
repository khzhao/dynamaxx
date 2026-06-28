# Scoring Notes

## Gate Status

- Fast gate: passed by verifying existing artifact `outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_polar_wind_taper.json`; `failed=False`, `issues=0`, primary score `-1.1232863545358902`.
- Iteration promotion gate: did not pass. Candidate primary score was `-1.1439751141779315`; incumbent primary score was `-1.143975258592661`; delta was `+1.444147295082132e-07`, below the required `+0.002`.
- Iteration diagnostics: clean for candidate and incumbent; both had `failed=False` and `issues=0`.
- Iteration guardrails: passed. Maximum early day 1-5 mean RMSE regression was `3.7026508155931215e-08`, below `0.02`; maximum variable+lead RMSE regression was `2.126336127121496e-07`, below `0.10`.
- Validation acceptance gate: not evaluated because the iteration promotion gate did not pass. Candidate validation was not run.

## Measurement Lessons

- Exact model-name filtering is required for these artifacts. The candidate fast, candidate iteration, and incumbent iteration JSON files each contained 120 records, of which 60 matched the evaluated model name and the remaining rows were persistence comparison rows.
- The polar wind taper behaves nearly identically to the incumbent on the iteration protocol. The primary delta and RMSE differences are at numerical-noise scale, with no meaningful guardrail regression.

## Anomalies

- Cache reuse: reused the supplied incumbent iteration and validation artifacts. Reused the candidate fast artifact after verifying model name, diagnostics, primary score, and exact-model row counts. The candidate iteration was newly run and reported `cached=0`.
- Resource limits: none observed. Candidate iteration used `--workers 4` with GPU dispatch and completed 229 chunks.
- Failed or restarted commands: none. `uv run pytest` exited 0; candidate iteration exited 0.
- Nonfinite or unstable outputs: none reported by diagnostics.

## Recommendation To Orchestrator

Report only the measured gate status: the candidate did not meet the iteration promotion threshold, while diagnostics and RMSE guardrails were clean. Do not treat this note as an accept or reject decision.

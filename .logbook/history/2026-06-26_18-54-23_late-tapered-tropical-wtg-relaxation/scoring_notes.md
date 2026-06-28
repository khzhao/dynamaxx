# Scoring Notes

## Gate Status

- Fast gate: passed from the provided handoff and verified artifact. `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_wtg_taper.json` reports primary score `-0.22392494621838646`, `failed=false`, `issues=0`, `records=120`, and `model_rows=60`.
- Iteration promotion gate: did not pass. Candidate iteration primary score was `-0.21983337873577272`; cached incumbent iteration primary score was `-0.2197104515448394`; signed delta was `-0.0001229271909333196`, below the required `+0.002` threshold.
- Iteration diagnostics and guardrails: diagnostics were clean with zero issues. Early day 1-5 mean RMSE guardrail passed for all variables, and no variable+lead RMSE regression exceeded the `+10%` guardrail.
- Validation acceptance gate: not evaluated. The fixed validation command was not run because iteration did not promote.
- Golden: not run.

## Commands And Status

- Used provided test record without rerun: `uv run pytest` had already passed with `261 passed`, `2 skipped` in `305.08s`.
- Used provided fast record after artifact verification: `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_wtg_taper` had already exited `0`.
- Ran candidate iteration exactly as requested: `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_wtg_taper --workers 4` exited `0`, completed `229/229` chunks, wrote `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_wtg_taper.json`, and reported `failed=False`, `issues=0`, `records=120`, primary score `-0.21983337873577272`.
- Computed guardrails from candidate and cached incumbent metrics JSON/CSV artifacts: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_wtg_taper.json`, `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_wtg_taper.csv`, `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`, and `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`.
- Did not run `uv run dynamaxx-eval validation --model dino_hsl2_mass_dse_wtg_vdse_wtg_taper --workers 4` because iteration did not promote.
- Did not rerun the incumbent.

## Cache Reuse

- Incumbent iteration metrics were reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json` and `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`.
- Incumbent iteration cache checks passed: requested incumbent matched the leaderboard incumbent, fingerprint fields matched, current HEAD matched `eval_code_commit` `ff40def55ac707e8915c840b856a0aaa3345b046`, fixed eval protocol files were not dirty, the artifact was readable, primary score was finite, JSON/CSV rows were present, and diagnostics were clean.
- Candidate source edits were not treated as cache invalidation because `roles/SCORER.md` states candidate source edits do not invalidate the accepted incumbent cache.
- Incumbent validation cache was not used for comparison because candidate validation was not run. The available cached paths are `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json` and `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`.

## Guardrail Details

- Early day 1-5 mean RMSE relative regressions: `10m_u_component_of_wind=+1.0701533604210597e-07`, `2m_temperature=+8.095161203453993e-08`, `geopotential_500=+1.7699136834368657e-07`, `mean_sea_level_pressure=+1.1056481625311689e-07`.
- Worst early day 1-5 mean RMSE regression: `geopotential_500`, `+1.7699136834368657e-07`, below the `+0.02` threshold.
- Worst variable+lead RMSE regression: `10m_u_component_of_wind` at lead `360h`, candidate RMSE `5.34748595122473`, incumbent RMSE `5.343150846633728`, relative regression `+0.0008113386118853491`, below the `+0.10` threshold.
- Variable+lead RMSE regressions over `+10%`: none.

## Artifacts

- Candidate fast: `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_wtg_taper.json`, `outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_wtg_taper.csv`.
- Candidate iteration: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_wtg_taper.json`, `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_wtg_taper.csv`.
- Candidate validation: not run; no candidate validation artifact was written by this scoring task.
- Incumbent iteration cache: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json`, `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`.
- Incumbent validation cache available but not used: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json`, `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv`.
- Score artifacts written here: `.logbook/history/2026-06-26_18-54-23_late-tapered-tropical-wtg-relaxation/scores.json` and `.logbook/history/2026-06-26_18-54-23_late-tapered-tropical-wtg-relaxation/scoring_notes.md`.

## Measurement Lessons

- The late tapered tropical WTG relaxation variant produced clean finite metrics but slightly worsened the iteration primary score relative to the cached incumbent.
- Guardrail movement was very small and clean; this result is about primary-score direction/size, not instability.

## Anomalies

- Cache reuse: no cache invalidation was found; incumbent iteration metrics were reused from the leaderboard pointer.
- Resource limits: no resource failure was observed during the candidate iteration run.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none reported by fast or iteration diagnostics.

## Recommendation To Orchestrator

Report the measured gate status above. The candidate did not promote to validation under the fixed iteration gate; the Scorer does not accept or reject the candidate.

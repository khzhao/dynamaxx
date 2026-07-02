# Scoring Notes

## Gate Status

- Fast gate: passed from verified existing artifact. `outputs/eval/fast_dino_ri2m_ekman_depth_orolift_theta.json` reports `failed=false`, 0 issues, 120 records, and primary score `-0.1329952445293929`.
- Iteration promotion gate: passed. Candidate primary `-0.13156559713631472` versus cached incumbent `-0.13590520069778708`, delta `+0.004339603561472366` against the `+0.002` threshold. Diagnostics were clean. Mean RMSE regressions over leads 1-5 days were all below `+2%`; the largest was Z500 at `+0.7788865200605566%`. The largest single variable/lead RMSE regression was Z500 day 2 at `+1.0575566129183667%`, below the `+10%` guardrail.
- Validation acceptance gate: measured as passed. Candidate primary `-0.13341144990707632` versus cached incumbent `-0.13767474868567484`, delta `+0.004263298778598518` against the `+0.001` threshold. Diagnostics were clean. Mean RMSE regressions over leads 1-5 days were all below `+2%`; the largest was Z500 at `+0.7110242616785794%`. The largest single variable/lead RMSE regression was Z500 day 2 at `+0.9455183193520166%`, below `+10%`.

## Guardrail Details

- Iteration early Z500: mean leads 1-5 days `+0.7788865200605566%`; per-lead values were `+0.8073569615362574%`, `+1.0575566129183667%`, `+0.8409523381423077%`, `+0.657178342852599%`, `+0.5313883448532525%`.
- Iteration early MSLP: mean leads 1-5 days `-2.205846359981465%`; per-lead values were `-1.1450419873230503%`, `-2.4076451856675764%`, `-2.4325475912219726%`, `-2.4872199470944205%`, `-2.5567770886003056%`.
- Validation early Z500: mean leads 1-5 days `+0.7110242616785794%`; per-lead values were `+0.7706447753141724%`, `+0.9455183193520166%`, `+0.7320870325806049%`, `+0.5803050542243223%`, `+0.5265661269217806%`.
- Validation early MSLP: mean leads 1-5 days `-2.253095816832107%`; per-lead values were `-1.1002613075368959%`, `-2.4255640757467885%`, `-2.566441522069745%`, `-2.592770748678758%`, `-2.580441430128347%`.

## Cache Reuse

- Iteration incumbent metrics were reused from `.logbook/leaderboard.json`: `outputs/eval/iteration_dino_ri2m_ekman_depth.json` and `outputs/eval/iteration_dino_ri2m_ekman_depth.csv`.
- Validation incumbent metrics were reused from `.logbook/leaderboard.json`: `outputs/eval/validation_dino_ri2m_ekman_depth.json` and `outputs/eval/validation_dino_ri2m_ekman_depth.csv`.
- Cache validation checks: requested incumbent matched `dino_ri2m_ekman_depth`; leaderboard fingerprint matched the fixed data path, target variables, lead range, and protocols; candidate edits did not touch fixed evaluation code; cached JSON files were readable, finite, and contained incumbent rows for primary-score and guardrail comparisons.
- No incumbent reruns were performed.

## Commands

- `uv run pytest`: exit 0, recorded from Orchestrator handoff as 288 passed, 2 skipped in 296.58s; not rerun by Scorer.
- `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_theta`: exit 0, recorded from Implementer handoff and verified from existing JSON artifact.
- `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_theta --workers 4`: exit 0, wrote `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_theta.json` and `.csv`.
- `uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth_orolift_theta --workers 4`: exit 0, wrote `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_theta.json` and `.csv`.
- `golden` was not run.

## Measurement Lessons

- The orographic-lift theta candidate improved primary score on both iteration and validation while keeping early Z500 regressions under 1.1% and improving early MSLP RMSE by roughly 2.2-2.3%.
- The known full-terrain failure mode around early Z500/MSLP did not appear here: MSLP improved, and Z500 worsened only mildly within fixed guardrails.

## Anomalies

- Command start timestamps were not captured by a wrapper; `scores.json` records artifact modification times as `finished_at` where available.
- The verified fast artifact is JSON only in the scorer record; no matching fast CSV was generated or required by the handoff.
- No failed or restarted commands.
- No nonfinite or unstable outputs were reported by diagnostics.

## Recommendation To Orchestrator

Report the measured gate status and caveats above. This Scorer report does not accept, reject, commit, or modify the leaderboard.

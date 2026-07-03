# Scoring Notes

## Gate Status

- Fast gate: passed before Scorer handoff; inherited result was `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind` exit 0, primary `-0.12943824136377413`, `failed=false`, issues `0`, records `120`.
- Iteration promotion gate: passed. Candidate primary `-0.1285119843716688`; cached incumbent primary `-0.13156559713631472`; delta `+0.0030536127646459132`, above the `+0.002` promotion threshold. Diagnostics were clean.
- Validation acceptance gate: passed by measurement. Candidate primary `-0.12911217353049617`; cached incumbent primary `-0.13341144990707632`; delta `+0.004299276376580147`, above the `+0.001` validation threshold. Diagnostics were clean.
- Guardrails: no early day 1-5 mean RMSE regressions exceeded `2%`; no variable-lead RMSE regressions exceeded `10%`.

## Cache Reuse

- Incumbent iteration was reused from `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_theta.json` and `.csv`.
- Incumbent validation was reused from `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_theta.json` and `.csv`.
- Cache checks passed: requested incumbent matched `.logbook/leaderboard.json`, leaderboard fingerprint covered `iteration` and `validation`, data path/targets/leads were compatible, artifacts were readable and finite, and each artifact contained 120 guardrail records.
- The current `HEAD` differs from the accepted eval commit only by accepted logbook/leaderboard artifacts; current source/test changes are candidate edits and do not invalidate the incumbent cache under `roles/SCORER.md`.
- No incumbent run was performed.

## Commands

- Inherited, not rerun by Scorer: `uv run pytest` -> exit 0, `294 passed, 2 skipped`.
- Inherited, not rerun by Scorer: `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_lwind` -> exit 0.
- Run by Scorer: `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_lwind --workers 4` -> exit 0.
- Run by Scorer: `uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth_orolift_lwind --workers 4` -> exit 0.
- Not run: incumbent iteration, incumbent validation, golden.

## Measurement Lessons

- The depth-weighted lower-column orographic-lift wind improved both iteration and validation primary scores by margins larger than the protocol thresholds.
- RMSE guardrail differences were effectively numerical-noise scale; the largest validation variable-lead relative regression was `1.1338433089983686e-09`.
- The candidate retained clean diagnostics across fast, iteration, and validation.

## Anomalies

- Cache reuse: successful for both incumbent protocols.
- Resource limits: none encountered.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none observed.

## Recommendation To Orchestrator

Report this as a measured gate pass and make the accept/reject decision in the Orchestrator role. Do not treat this Scorer note as a commit or leaderboard update.

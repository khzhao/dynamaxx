# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_hsl2_theta_dse_hsl` exited 0 with `failed=False`, `issues=0`, 120 records, and candidate primary score `-0.267644797202895`.
- Iteration promotion gate: passed. Candidate primary score `-0.267373732174336` versus cached incumbent `-0.312828905433362` gives delta `+0.045455173259027`, above the `+0.002` threshold. Candidate diagnostics were clean. The largest early lead 1-5 day mean RMSE regression was `-1.562778%`, and the worst variable/lead RMSE regression was `-0.062593%` at `10m_u_component_of_wind` day `1`.
- Validation acceptance gate: measured as passed by the fixed scoring criteria. Candidate primary score `-0.265481976988276` versus cached incumbent `-0.307237434599918` gives delta `+0.041755457611642`, above the `+0.001` threshold. Candidate diagnostics were clean. The largest early lead 1-5 day mean RMSE regression was `-1.562695%`, and the worst variable/lead RMSE regression was `-0.061347%` at `10m_u_component_of_wind` day `1`.

## Measurement Lessons

- Lesson: DSE horizontal semilagrangian transport produced broad RMSE improvements in both iteration and validation. The weakest guardrail improvement was day-1 `10m_u_component_of_wind`, but it was still an RMSE improvement rather than a regression.
- Lesson: Candidate improvements were similar across iteration and validation deltas (`+0.045455` and `+0.041755`), so this measurement did not show an obvious validation-only overfit signal.

## Anomalies

- Cache reuse: incumbent iteration and validation metrics were reused from `.logbook/leaderboard.json` artifacts: `outputs/eval/iteration_dino_hsl2_theta.json`, `outputs/eval/iteration_dino_hsl2_theta.csv`, `outputs/eval/validation_dino_hsl2_theta.json`, and `outputs/eval/validation_dino_hsl2_theta.csv`. The requested incumbent matched the leaderboard incumbent, the fingerprint was compatible, current HEAD matched the leaderboard eval code commit, and the artifacts were readable with finite primary scores and guardrail rows. No incumbent rerun was performed.
- Resource limits: no resource failures were observed. Iteration used 4 effective GPU workers over 229 chunks; validation used 4 effective GPU workers over 46 chunks.
- Failed or restarted commands: the first registration probe failed because it imported nonexistent helper `registered_model_names`. The corrected registry command using `dycore_model_names` succeeded and confirmed both models. No evaluation command was restarted.
- Nonfinite or unstable outputs: none observed in fast, iteration, or validation diagnostics (`failed=False`, `issues=0` for each candidate protocol).

## Recommendation To Orchestrator

The scorer measurement shows clean fast, iteration, and validation diagnostics, positive primary-score deltas versus the cached incumbent, and no fixed RMSE guardrail violations. Validation was run exactly once after the iteration promotion gate passed. Orchestrator should make the decision and perform any required leaderboard or cleanup actions.

# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_wtg_narrow` exited `0`, `failed=false`, issues `0`, records `120`, primary `-0.2244004137048363`.
- Iteration promotion gate: failed. `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_wtg_narrow --workers 4` exited `0`, `failed=false`, issues `0`, records `120`, primary `-0.2203902442291438`.
- Validation acceptance gate: not run. Iteration delta was `-0.0006797926843044033` versus cached incumbent score `-0.2197104515448394`.

## Measurement Lessons

- Narrowing the tropical WTG latitude support weakened the accepted
  pressure-ramped WTG incumbent under the iteration protocol.
- The candidate slightly improved early Z500 mean RMSE but degraded wind and
  MSLP enough to reduce the primary score.

## Anomalies

- Cache reuse: incumbent iteration metrics were reused from
  `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json` and `.csv`.
  The leaderboard cache was valid; no incumbent rerun was performed.
- Resource limits: none. The iteration run completed with 4 workers on local
  WeatherBench2 data.
- Failed or restarted commands: none. Formatting was required and corrected
  before final focused tests and scoring.
- Nonfinite or unstable outputs: none. Candidate fast and iteration diagnostics
  were clean.

## Recommendation To Orchestrator

Reject the candidate. It passed diagnostics, but iteration was worse than the
cached incumbent, so validation should remain skipped and the implementation
should be reverted.

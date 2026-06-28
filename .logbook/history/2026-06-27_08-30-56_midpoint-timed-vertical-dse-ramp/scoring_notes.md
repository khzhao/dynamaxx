# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_ramp_midtime` exited `0`, `failed=false`, issues `0`, records `120`, primary `-0.22376081825519012`.
- Iteration promotion gate: failed. `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_ramp_midtime --workers 4` exited `0`, `failed=false`, issues `0`, records `120`, primary `-0.2196613024621508`.
- Validation acceptance gate: not run. Iteration delta was only `+0.000049149082688604295` versus cached incumbent score `-0.2197104515448394`, below the fixed `+0.002` promotion threshold.

## Measurement Lessons

- Midpoint sampling of the vertical-DSE ramp is numerically clean but effectively
  neutral under the iteration protocol.
- The small primary improvement is far below the protocol threshold and should
  not be treated as evidence for accepting or validating this candidate.

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

Reject the candidate. It passed diagnostics and guardrails, but the iteration
delta did not meet the fixed promotion threshold, so validation should remain
skipped and the implementation should be reverted.

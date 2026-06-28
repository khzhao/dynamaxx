# Scoring Notes

## Gate Status

- Fast gate: failed. `uv run dynamaxx-eval fast --model dinosaur_moist` exited 0, but the fixed fast diagnostics reported `failed=true`.
- Iteration promotion gate: not run. The fast gate failed, so candidate and incumbent iteration scoring were not reached.
- Validation acceptance gate: not run. Validation was not allowed after the failed fast diagnostic.

## Measurement Lessons

- The moist virtual-temperature candidate produced nonfinite forecast values during the fast diagnostic. Future work on this idea should isolate the instability source before any full iteration or validation scoring.

## Anomalies

- Cache reuse: none. Scorer reused the implementer-provided fast artifacts at `outputs/eval/fast_dinosaur_moist.json` and `outputs/eval/fast_dinosaur_moist.csv` rather than rerunning the gate.
- Resource limits: none encountered. Full-gate resources were available, but the fast failure made full scoring ineligible.
- Failed or restarted commands: no command reruns or restarts by Scorer. The fast evaluation command exited 0, but diagnostic checks failed.
- Nonfinite or unstable outputs: fast diagnostics reported one error, `nonfinite_forecast`, with value `4713420` and message `Forecast contains NaN or Inf values.`

## Recommendation To Orchestrator

Report `dinosaur_moist` as a failed fast-gate measurement with candidate fast primary score `-1.7976931348623157e+308`. Do not run iteration or validation for this artifact; route the idea back for stability diagnosis or select the next ready proposal.

# Scoring Notes

## Gate Status

- Fast gate: failed. `uv run dynamaxx-eval fast --model dino_hsl_cflblend`
  completed but diagnostics reported nonfinite forecast values and nonfinite
  metric records. The primary score was the negative finite sentinel
  `-1.7976931348623157e+308`.
- Iteration gate: not run because fast diagnostics failed.
- Validation gate: not run because iteration did not run.
- Golden: not run.

## Repair Attempt

The initial linear CFL blend produced nonfinite forecasts. The Orchestrator
made one bounded repair inside the selected proposal: the local displacement
weight was changed from linear CFL weight to square-root CFL weight, preserving
the zero-displacement Eulerian endpoint and capped-displacement HSL endpoint.
Ruff, focused tests, and full `uv run pytest` passed after the repair.

The repaired candidate still failed the fast gate with the same diagnostic
class, so the candidate was treated as scientifically or numerically unstable
under the fixed protocol.

## Cache Reuse

No incumbent iteration or validation artifacts were needed because the candidate
did not pass the fast gate. No incumbent evaluation was run.

## Artifacts

- Candidate fast: `outputs/eval/fast_dino_hsl_cflblend.json`,
  `outputs/eval/fast_dino_hsl_cflblend.csv`.
- Candidate diff:
  `.logbook/history/2026-06-22_17-36-00_cfl-blended-hsl-theta/candidate.diff`.

## Lessons

- A pointwise blend between Eulerian theta tendency and accepted midpoint HSL
  theta tendency destabilized the rollout even when biased toward the accepted
  HSL path.
- The accepted all-HSL replacement appears safer than spatially varying CFL
  blending for this dycore family.

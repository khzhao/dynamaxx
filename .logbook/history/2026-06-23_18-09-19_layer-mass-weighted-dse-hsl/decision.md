# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.2616483974683927`
- Iteration incumbent primary score: `-0.26737373217433574`
- Iteration delta: `+0.005725334705943053`
- Validation candidate primary score: `-0.2600180396322455`
- Validation incumbent primary score: `-0.2654819769882763`
- Validation delta: `+0.00546393735603079`

## Rationale

The candidate exceeded the fixed iteration promotion threshold of `+0.002`
and the fixed validation acceptance threshold of `+0.001` against the cached
incumbent metrics. The incumbent cache was valid: the leaderboard incumbent
matched `dino_hsl2_theta_dse_hsl`, the accepted baseline commit was
`a274541cc57f593b8e5796e1df8307e8820c2d6b`, the fixed WeatherBench2 data path
and metric surface matched, and the cached incumbent artifacts were readable,
finite, complete, and clean.

Candidate fast, iteration, and validation diagnostics were clean with
`failed=False` and zero issues. Golden was not run. Early day 1-5 mean RMSE
regressions were far below the `2%` guardrail on both iteration and validation.
The worst iteration variable+lead RMSE regression was mean sea level pressure
at day 5 with `+1.7141834768660351e-09` relative regression, and the worst
validation variable+lead RMSE regression was mean sea level pressure at day 11
with `+6.492272688853867e-09` relative regression, both far below the `10%`
guardrail.

The implementation is physically plausible as a conservative local restaging
of the accepted DSE-HSL thermal transport: it transports `delta_p * DSE`
anomaly horizontally, divides by guarded local layer pressure thickness, keeps
the incumbent vertical theta and adiabatic terms, and falls back to the
incumbent DSE-HSL tendency on unsafe diagnostics. The fixed forecast contract
and evaluation protocol were unchanged.

## Lessons Learned

- Layer-mass weighting the accepted DSE-HSL scalar transport improves the
  primary iteration and validation scores while leaving fixed RMSE guardrails
  effectively unchanged at numerical-noise scale.
- The cached incumbent artifacts were sufficient for comparison; no incumbent
  rerun was necessary.

## Cleanup Completed

- Candidate code retained or reverted: retained for acceptance and committed.
- Research state updated: removed `.logbook/research/ready/layer-mass-weighted-dse-hsl.md`.
- Leaderboard updated: updated after the acceptance commit with the new incumbent and artifacts.
- Git status checked: tracked source/test tree clean after commit.

## Next Action

Continue the optimization loop with a fresh research/evaluation/implementation
iteration.

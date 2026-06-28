# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.22588531808146894`
- Iteration incumbent primary score: `-0.2197104515448394`
- Iteration delta: `-0.006174866536629547`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.21940899263836755`
- Validation delta: not applicable

## Rationale

The candidate failed the fixed iteration promotion gate. Its iteration primary
score was worse than the cached incumbent by `-0.006174866536629547`, below the
required `+0.002` promotion threshold. Candidate fast and iteration diagnostics
were clean, but clean diagnostics are not sufficient for promotion.

The early day 1-5 mean RMSE guardrail also failed. The largest early mean
regression was `2m_temperature` at `+2.6769825875213316%`, above the `2%`
limit. The worst variable+lead RMSE guardrail passed; the worst single-lead
regression was `2m_temperature` at 48h with `+4.605687366818319%`, below the
`10%` limit.

The incumbent iteration metrics were reused from the leaderboard cache and no
incumbent rerun was performed. Validation and golden were not run because
iteration did not promote.

## Lessons Learned

- Introducing the internal zero-column-mean vertical-DSE component earlier than
  the accepted external-mode ramp degraded the primary score and worsened early
  2m-temperature RMSE.
- The accepted pressure-ramped vertical-DSE increment appears sensitive to
  early internal thermal redistribution, not only to column/external pressure
  shock.
- Future vertical-DSE refinements should be skeptical of earlier thermal spinup
  unless they directly guard lower-tropospheric temperature error.

## Cleanup Completed

- Candidate code retained or reverted: reverted with the saved candidate diff.
- Research state updated: removed
  `.logbook/research/ready/baroclinic-mode-vertical-dse-spinup.md`.
- Leaderboard updated: not updated because the candidate was rejected.
- Git status checked: tracked source/test tree returned to clean after rollback;
  pre-existing untracked `gifs/` directory preserved.

## Next Action

Continue the optimization loop with a new Researcher/Evaluator cycle using
`dino_hsl2_mass_dse_wtg_vdse_ramp` as the incumbent.

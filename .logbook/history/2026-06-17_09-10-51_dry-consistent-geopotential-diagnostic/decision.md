# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.1442516002936804`
- Iteration incumbent primary score: `-1.143975258592661`
- Iteration delta: `-0.00027634170101942246`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1301883620649706`
- Validation delta: not run

## Rationale

The candidate passed fast diagnostics and the full test suite, but it failed the
iteration promotion gate. Its primary score regressed by
`-0.00027634170101942246`, below the required `+0.002` threshold, and validation
was not run.

It also failed the variable+lead RMSE guardrail. `geopotential_500` at 24 h
regressed by `+19.566144167188776%`, exceeding the `10%` limit. The early day
1-5 mean RMSE guardrail remained below `2%`, but the short-lead Z500 regression
is sufficient to reject the candidate even without the negative primary delta.

The result shows that the passive-humidity virtual-temperature diagnostic is
beneficial for first-day Z500 in the fixed benchmark, even though the rollout
dynamics are dry. Internal dry consistency alone is not a better scoring
diagnostic for this incumbent.

## Lessons Learned

- Removing humidity from geopotential reconstruction damages day-1
  `geopotential_500`; the virtual-temperature diagnostic should remain in the
  incumbent output path.
- Output-only changes can be stable and localized yet fail a variable+lead
  guardrail, so future output diagnostics need strict short-lead checks before
  iteration expectations are trusted.
- Non-geopotential target changes were roundoff-scale, which confirms the
  implementation isolation but not the scientific hypothesis.

## Cleanup Completed

- Candidate code retained or reverted: reverted; no source/test changes
  retained.
- Research state updated: consumed ready proposal removed after preserving it
  in this history directory.
- Leaderboard updated: no; incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
- Git status checked: completed after rollback.

## Next Action

Continue the optimization loop from the existing incumbent and re-triage the
remaining staged proposals or request new Researcher proposals if needed.

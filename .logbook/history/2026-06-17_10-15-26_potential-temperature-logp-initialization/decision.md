# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.1448887048318772`
- Iteration incumbent primary score: `-1.143975258592661`
- Iteration delta: `-0.0009134462392161868`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1301883620649706`
- Validation delta: not run

## Rationale

The candidate passed the fast sanity gate and produced clean iteration
diagnostics with `failed=false` and `issues=0`, but it did not meet the fixed
iteration promotion threshold. The primary score delta was negative
(`-0.0009134462392161868`) versus the required `+0.002`, so validation was not
run.

The guardrails were clean. The largest early day 1-5 mean RMSE regression was
`geopotential_500` at `+0.060270%`, well below the 2% threshold. The largest
single variable+lead RMSE regression was `mean_sea_level_pressure` at 168h with
`+0.144944%`, well below the 10% threshold. These measurements indicate a
stable but broadly sub-skill thermodynamic remap, not a localized numerical
failure.

## Lessons Learned

- Dry-potential-temperature log-pressure remapping is numerically stable for
  this incumbent but does not improve fixed iteration skill.
- Future temperature-initialization proposals need a mechanism beyond changing
  the interpolated thermodynamic variable, because the current aggregate loss
  was broad and guardrail-clean.
- Wind, humidity, DFI, and output paths can remain on the accepted incumbent
  path for later initialization experiments; the failure here was not caused by
  diagnostics or contract changes.

## Cleanup Completed

- Candidate code retained or reverted: reverted the candidate source and test
  changes from the six touched files.
- Research state updated: ready proposal removed after immutable history record
  was completed.
- Leaderboard updated: no; incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
- Git status checked: tracked worktree clean on branch `kzhao--codex`.

## Next Action

Revert the candidate implementation changes, verify tracked worktree
cleanliness, then start the next optimization iteration from the remaining
staged research queue.

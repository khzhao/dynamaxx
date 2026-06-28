# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.8353205623225486`
- Iteration incumbent primary score: `-0.8348806410796545`
- Iteration delta: `-0.000439921242894048`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.8200230307466544`
- Validation delta: not run

## Rationale

The candidate failed the fixed iteration promotion gate. The primary score
delta was negative, below the required `+0.002` threshold, so validation was
not allowed under the protocol.

Diagnostics were clean and guardrails passed. Early day 1-5 mean RMSE regressed
by only `+0.022907203220216124%`, below the `+2%` guardrail, and the largest
variable+lead RMSE regression was `mean_sea_level_pressure` day 15 at
`+0.13102801215607499%`, below the `+10%` guardrail. The implementation was
therefore numerically stable but did not improve the fixed selection metric.

## Lessons Learned

- The 50/50 scalar split-form change was nearly neutral at RMSE level but
  slightly harmful to the primary score aggregation.
- Future scalar-transport ideas need a sharper mechanism than formal
  conservative/advective symmetry alone, especially after the accepted
  theta-form tendency has already improved thermal transport.
- Pressure-related side effects remain small but should continue to be watched,
  since the largest regression was again in `mean_sea_level_pressure`.

## Cleanup Completed

- Candidate code retained or reverted: reverted. No source or test changes from
  this rejected candidate remain in the tracked worktree.
- Research state updated: proposal, implementation, scores, scoring notes,
  decision, and artifact manifest are recorded under
  `.logbook/history/2026-06-18_20-37-51_theta-skew-symmetric-scalar-advection/`.
- Leaderboard updated: no. The incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency`
  at `cb5bbd1c15744b4fc00ecca5de78da188685a33d`.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Start the next iteration immediately. The user explicitly removed
idea-exhaustion as a stop condition, so the Researcher must continue producing
new ideas.

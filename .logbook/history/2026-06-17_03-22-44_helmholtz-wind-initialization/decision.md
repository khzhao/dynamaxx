# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.5597543505393903`
- Iteration incumbent primary score: `-1.2155220438349765`
- Iteration delta: `-0.34423230670441374`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.2028991078287248`
- Validation delta: not run

## Rationale

The candidate passed fast diagnostics and iteration diagnostics with zero
issues, but failed the fixed iteration promotion gate decisively. The iteration
primary delta was `-0.34423230670441374`, far below the required `+0.002`
threshold. The early mean RMSE guardrail failed for `geopotential_500` and
`mean_sea_level_pressure`, with day-1-through-day-5 mean regressions of about
21.6% and 21.4%. The variable+lead RMSE guardrail also failed with 30
regressing rows above 10%; the largest relative regression was `56.297419%` for
`geopotential_500` at lead `360h`.

Validation was correctly skipped because iteration promotion failed. The
candidate cannot become incumbent under the fixed protocol.

## Lessons Learned

- Initializing vorticity and divergence through scalar Helmholtz diagnostics was
  finite but substantially worsened mass and geopotential balance.
- The accepted log-pressure initialization benefit appears specific to
  thermodynamic/vector-field remapping as currently implemented; changing the
  wind control-variable projection disrupted pressure/geopotential evolution.
- Future wind-initialization proposals need explicit mass/geopotential balance
  protection before spending a full iteration run.

## Cleanup Completed

- Candidate code retained or reverted: reverted after preserving this history
  record.
- Research state updated: selected ready proposal copied into this immutable
  history directory; ready copy removed after rejection.
- Leaderboard updated: no, incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init`.
- Git status checked: yes, tracked worktree clean after rollback.

## Next Action

Start the next continuous-loop iteration with
`dinosaur_dfi_surface_residual_weak_hs_logp_init` still as incumbent. The
remaining ready proposal is `layer-mean-thermal-recentering`.

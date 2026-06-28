# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.8348723734291655`
- Iteration incumbent primary score: `-0.8348806410796545`
- Iteration delta: `+0.000008267650489002243`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.8200230307466544`
- Validation delta: not run

## Rationale

The candidate failed the fixed iteration promotion gate. Its primary score
delta was positive but far below the required `+0.002` threshold, so validation
was not allowed under the protocol.

Diagnostics were clean and RMSE guardrails passed. Early day 1-5 mean RMSE
changed by only `+0.00009828690376106599%`, below the `+2%` guardrail, and the
largest variable+lead RMSE regression was `10m_u_component_of_wind` day 12 at
`+0.00507268124075087%`, far below the `+10%` guardrail. The candidate was
therefore stable and nearly neutral, but not meaningfully better than the
incumbent.

## Lessons Learned

- Converting the weak Held-Suarez relaxation to theta space is almost
  algebraically neutral under this implementation and fixed evaluation.
- Future theta-forcing proposals need a larger or more localized mechanism than
  same-pressure temperature/theta conversion with unchanged relaxation
  coefficients.
- The accepted temperature-space weak-HS source remains the incumbent behavior.

## Cleanup Completed

- Candidate code retained or reverted: reverted. No source or test changes from
  this rejected candidate remain in the tracked worktree.
- Research state updated: proposal, implementation, scores, scoring notes,
  decision, and artifact manifest are recorded under
  `.logbook/history/2026-06-18_22-27-09_theta-consistent-held-suarez-forcing/`.
- Leaderboard updated: no. The incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency`
  at `cb5bbd1c15744b4fc00ecca5de78da188685a33d`.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Start the next iteration immediately. The user explicitly removed
idea-exhaustion as a stop condition, so the Researcher must continue producing
new ideas.

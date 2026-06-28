# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.8348806410796545`
- Iteration incumbent primary score: `-0.8503285831632285`
- Iteration delta: `+0.015447942083573918`
- Validation candidate primary score: `-0.8200230307466544`
- Validation incumbent primary score: `-0.8392576077353403`
- Validation delta: `+0.019234576988685914`

## Rationale

The candidate passed every fixed acceptance gate. The iteration delta exceeded
the `+0.002` promotion threshold, the validation delta exceeded the `+0.001`
acceptance threshold, diagnostics were clean, and no RMSE guardrail violation
was observed.

Early day 1-5 mean RMSE regressed by `+0.5350022340658391%` on iteration and
`+0.15635222687726263%` on validation, both below the `+2%` threshold. The
largest variable+lead RMSE regressions were `mean_sea_level_pressure` day 1 at
`+1.7579965544157576%` on iteration and `+1.6361908236509046%` on validation,
both well below the `+10%` guardrail.

The measured benefit is consistent with the proposal: the theta-form explicit
thermal tendency improved primary score on both fixed splits, with its clearest
RMSE gains in `2m_temperature` around medium leads and modest 10 m wind gains.
The main cost was small early pressure and geopotential degradation that stayed
inside protocol limits.

## Lessons Learned

- A theta-form explicit thermodynamic tendency can improve the current
  Dinosaur incumbent without changing initialization, DFI span, Coriolis
  splitting, residual correction, or 10 m wind diagnostics.
- The incumbent still has exploitable non-wind error after the Richardson 10 m
  diagnostic gain; future research should continue targeting thermal balance
  and pressure/geopotential side effects rather than only wind diagnostics.
- Future theta-family proposals should account for the observed day-1
  `mean_sea_level_pressure` sensitivity.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed in
  `cb5bbd1c15744b4fc00ecca5de78da188685a33d`.
- Research state updated: proposal, implementation, scores, scoring notes,
  decision, and artifact manifest are recorded under
  `.logbook/history/2026-06-18_18-48-01_potential-temperature-thermodynamic-tendency/`.
- Leaderboard updated: yes, incumbent now points to
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency`.
- Git status checked: tracked worktree clean after commit.

## Next Action

Start the next iteration immediately. The user explicitly removed
idea-exhaustion as a stop condition, so the Researcher must continue producing
new ideas.

# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.8308832822743712`
- Iteration incumbent primary score: `-0.8348806410796545`
- Iteration delta: `+0.003997358805283291`
- Validation candidate primary score: `-0.8148379476593253`
- Validation incumbent primary score: `-0.8200230307466544`
- Validation delta: `+0.005185083087329123`

## Rationale

The candidate passed every fixed acceptance gate. The iteration delta exceeded
the `+0.002` promotion threshold, the validation delta exceeded the `+0.001`
acceptance threshold, and candidate diagnostics were clean on fast, iteration,
and validation.

The early day 1-5 aggregate RMSE guard improved slightly on both scored splits:
`-0.049012852833619176%` on iteration and `-0.050326924901449965%` on
validation. The largest variable-by-lead RMSE regressions were late
`10m_u_component_of_wind`: day 15 at `+8.010338959282189%` on iteration and
day 15 at `+7.039021793195873%` on validation, both below the `+10%`
guardrail.

The result supports the hypothesis that suppressing horizontally uniform dry
theta drift still improves the current theta-tendency Dinosaur incumbent. The
main tradeoff is late 10 m zonal wind degradation that remains within the fixed
guardrail.

## Lessons Learned

- Layer-mean theta recentering recovers enough thermal-balance signal to clear
  both fixed model-selection splits after the accepted Richardson 10 m wind
  diagnostic.
- Future thermal-balance proposals should watch late `10m_u_component_of_wind`,
  because the limiting regression moved from early wind to late wind.
- The accepted candidate improves `2m_temperature` most clearly near medium
  leads while leaving early aggregate RMSE slightly better than the incumbent.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed in
  `c359ee1b016ccd92412585997a799a7c644a65c5`.
- Research state updated: proposal, implementation, scores, scoring notes,
  decision, and artifact manifest are recorded under
  `.logbook/history/2026-06-19_00-02-28_theta-zero-mode-thermal-recentering/`.
- Leaderboard updated: yes, incumbent now points to
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter`.
- Git status checked: tracked worktree clean after commit.

## Next Action

Start the next iteration immediately. The user explicitly removed idea
exhaustion as a stop condition, so the Researcher must continue producing new
ideas without end unless paused by the user or blocked by infrastructure.

# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.8503285831632285`
- Iteration incumbent primary score: `-1.1021997794865541`
- Iteration delta: `+0.25187119632332566`
- Validation candidate primary score: `-0.8392576077353403`
- Validation incumbent primary score: `-1.0904774361507537`
- Validation delta: `+0.25121982841541335`

## Rationale

The candidate passed every fixed acceptance gate. The iteration delta was far
above the `+0.002` promotion threshold, the validation delta was far above the
`+0.001` acceptance threshold, diagnostics were clean, and no RMSE guardrail
violations were observed.

The measured improvement is concentrated in the intended channel:
`10m_u_component_of_wind`. Iteration day 1-5 mean RMSE improved by
`41.98594983550589%` for that channel, while `2m_temperature`,
`geopotential_500`, and `mean_sea_level_pressure` were effectively unchanged.
Validation showed the same pattern, and the largest positive variable+lead
regressions were tiny: iteration `geopotential_500` day 13 at
`0.0014906100606845295%`, and validation `2m_temperature` day 14 at
`0.0024576258722063763%`.

## Lessons Learned

- A bounded raw 10 m wind diagnostic can substantially improve the fixed target
  wind metric while preserving the accepted residual correction and mass-field
  behavior.
- This result is strong evidence that the lowest sigma-layer wind was a poor
  direct proxy for the scored 10 m wind after the residual correction improved
  surface diagnostics.
- Future Researcher proposals should treat this Richardson-bounded 10 m wind
  diagnostic as incumbent behavior and avoid near-duplicate wind amplitude
  rescalings unless they introduce a materially different physical signal.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed in
  `257f79d871482727b4256b624490122a84982c69`.
- Research state updated: proposal moved to immutable history at
  `.logbook/history/2026-06-18_17-23-29_surface-layer-richardson-wind-diagnostic/`.
- Leaderboard updated: yes, incumbent now points to
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind`.
- Git status checked: tracked worktree clean after commit.

## Next Action

Start the next iteration immediately. The user explicitly removed idea-exhaustion
as a stop condition, so the Researcher must continue producing new ideas.

# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-1.1021997794865541`
- Iteration incumbent primary score: `-1.1241936221835356`
- Iteration delta: `+0.021993842696981458`
- Validation candidate primary score: `-1.0904774361507537`
- Validation incumbent primary score: `-1.1127999773519712`
- Validation delta: `+0.02232254120121757`

## Rationale

The candidate passed every fixed acceptance gate. Iteration exceeded the
`+0.002` promotion threshold, validation exceeded the `+0.001` acceptance
threshold, diagnostics were clean, and no RMSE guardrail violations were
observed on either protocol.

The improvement is concentrated in near-surface diagnostics, as intended.
Iteration day 1-5 mean RMSE improved by `6.439308090963196%` for
`2m_temperature` and `0.5763218836489706%` for `10m_u_component_of_wind`.
Validation showed the same pattern: `2m_temperature` improved by
`6.42346079582575%` and `10m_u_component_of_wind` by
`0.5833540638885769%`. Mass-field movement was effectively neutral: the largest
positive iteration variable+lead RMSE regression was `mean_sea_level_pressure`
day 14 at `0.001043216021196686%`, and the largest validation regression was
`geopotential_500` day 9 at `0.0005729220533994537%`.

## Lessons Learned

- Refining the already accepted near-surface residual mechanism with a bounded
  local decay field can produce large primary-score gains without perturbing
  pressure or geopotential diagnostics.
- The result supports more careful output-diagnostic work around near-surface
  channels, but not broad validation-tuned residual sweeps.
- Future Researcher proposals should treat stability-aware residual decay as
  the new incumbent behavior and avoid duplicate residual-decay variants unless
  they introduce a distinct physical signal.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed in
  `5cdb5ba7bd929dc6f29eba14da306f1ce5f6eb81`.
- Research state updated: proposal moved to immutable history at
  `.logbook/history/2026-06-18_15-57-11_stability-aware-surface-residual-decay/`.
- Leaderboard updated: yes, incumbent now points to
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual`.
- Git status checked: tracked worktree clean after commit.

## Next Action

Start the next iteration immediately. The user explicitly removed idea-exhaustion
as a stop condition, so the Researcher must continue producing new ideas.

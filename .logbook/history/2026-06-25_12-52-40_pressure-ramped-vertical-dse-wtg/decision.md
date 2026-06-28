# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.2197104515448394`
- Iteration incumbent primary score: `-0.25851235493825614`
- Iteration delta: `+0.03880190339341674`
- Validation candidate primary score: `-0.21940899263836755`
- Validation incumbent primary score: `-0.25704033104116597`
- Validation delta: `+0.03763133840279842`

## Rationale

The candidate passed all fixed selection gates. Fast, iteration, and validation
diagnostics were clean with zero issues. The iteration delta exceeded the
`+0.002` promotion threshold, and validation exceeded the `+0.001` acceptance
threshold.

The fixed RMSE guardrails also passed. Iteration's largest early day 1-5 mean
RMSE regression was `6.336602353940179e-10`, and its worst variable+lead RMSE
regression was `10m_u_component_of_wind` at 192h with
`3.9195791057267115e-09`, both far below their thresholds. Validation's largest
early day 1-5 mean RMSE regression was `3.0178144427850384e-09`, and its worst
variable+lead RMSE regression was `geopotential_500` at 48h with
`9.176133852761836e-09`, again far below the fixed limits.

The incumbent iteration and validation artifacts were reused from
`.logbook/leaderboard.json`; no incumbent rerun was performed. This was valid
because the requested incumbent matched the leaderboard incumbent, the cached
artifacts were present, readable, finite, and complete, and the fixed
evaluation fingerprint remained compatible.

## Lessons Learned

- The prior unrestricted vertical-DSE mechanism's large aggregate signal can be
  recovered on the current WTG incumbent while avoiding the earlier day-1 MSLP
  shock.
- The fixed zero-through-24h, full-by-72h ramp plus broad-mode spinup guard is a
  useful pattern for high-signal thermal mechanisms that otherwise damage early
  pressure balance.
- The leaderboard cache policy avoided a wasteful incumbent rerun while still
  preserving a valid candidate-versus-incumbent comparison.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as
  `ff40def55ac707e8915c840b856a0aaa3345b046`.
- Research state updated: selected ready proposal will be removed from
  `.logbook/research/ready` after this decision record is written.
- Leaderboard updated: updated to `dino_hsl2_mass_dse_wtg_vdse_ramp` with
  iteration and validation cached artifacts.
- Git status checked: tracked source/test changes were committed; pre-existing
  untracked `gifs/` directory preserved.

## Next Action

Continue the optimization loop with a new Researcher/Evaluator cycle using
`dino_hsl2_mass_dse_wtg_vdse_ramp` as the incumbent.

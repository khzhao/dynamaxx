# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: `-1.1339683809399665`
- Iteration candidate primary score: `-1.1703668264356009`
- Iteration incumbent primary score: `-1.143975258592661`
- Iteration delta: `-0.026391567842939834`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1301883620649706`
- Validation delta: not run

## Rationale

The candidate passed the full test suite, the fast gate, and iteration
diagnostics, but failed the fixed iteration promotion gate. The iteration
primary score regressed by `-0.026391567842939834`, which is below the required
`+0.002` improvement, so validation was not run.

The early day 1-5 target-variable mean RMSE guardrail also failed for three
variables. `mean_sea_level_pressure` regressed by `+3.838807583070794%`,
`geopotential_500` regressed by `+3.479620810633745%`, and
`10m_u_component_of_wind` regressed by `+3.4879883059549054%`, all above the
`2%` threshold. `2m_temperature` improved by `-0.6801705293931391%`, but not
enough to offset the pressure, height, and wind degradation.

No individual target variable plus lead RMSE regression exceeded the `10%`
guardrail. The worst variable-plus-lead movement was `geopotential_500` at
`288` hours with `+6.280739941335689%`. Diagnostics were clean with
`failed=False` and `issues=0`, so the rejection is based on skill and early
RMSE guardrails rather than numerical instability.

## Lessons Learned

- Bounded warm-liquid saturation adjustment can run cleanly in the current
  Dinosaur rollout and improves the fast primary score relative to the
  incumbent's iteration baseline, but it does not improve the fixed iteration
  protocol.
- Local supersaturation removal plus latent heating improved early
  `2m_temperature` RMSE but degraded mass, height, and wind fields, indicating
  that this minimal moist-physics closure perturbs balanced evolution more than
  it helps the aggregate WeatherBench2 score.
- Future humidity proposals should not simply add irreversible moist heating
  inside the dycore without a stronger closure or a separately reviewed
  evaluation-infrastructure reason to inspect additional moist diagnostics.

## Cleanup Completed

- Candidate code retained or reverted: reverted the six modified source and
  test files; no rejected code remains in tracked files.
- Research state updated: selected ready proposal was moved into this immutable
  history directory before implementation.
- Leaderboard updated: no; incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
- Git status checked: tracked worktree clean on branch `kzhao--codex`.

## Next Action

Revert the six candidate implementation files, verify the tracked worktree is
clean, then continue the loop by asking Researcher for any genuinely new
non-duplicate mechanism. If no ready or researchable ideas remain after a
documented search and triage, record the protocol stop condition.

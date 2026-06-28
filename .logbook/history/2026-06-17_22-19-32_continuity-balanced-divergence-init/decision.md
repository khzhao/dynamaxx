# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: `-1.1241672381984182`
- Iteration candidate primary score: `-1.1452881585043542`
- Iteration incumbent primary score: `-1.143975258592661`
- Iteration delta: `-0.001312899911693144`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1301883620649706`
- Validation delta: not run

## Rationale

The candidate passed the full test suite, the fast gate, iteration diagnostics,
and all fixed RMSE guardrails, but it failed the fixed iteration promotion gate.
The iteration primary score regressed by `-0.001312899911693144`, below the
required `+0.002` improvement, so validation was not run.

The RMSE guardrails were clean. Day 1-5 mean RMSE improved slightly for
`10m_u_component_of_wind`, `geopotential_500`, and
`mean_sea_level_pressure`; `2m_temperature` regressed by only
`+0.05211582634453378%`, below the `2%` threshold. No individual target
variable plus lead RMSE regression exceeded the `10%` threshold. The worst was
`geopotential_500` at `24` hours with `+1.34568441989434%`.

The physical lesson is that the bounded one-time divergence-only continuity
correction is stable and can improve early mass and height RMSE, but it does
not improve the aggregate iteration primary score. The failure is skill-based,
not a numerical diagnostic or guardrail failure.

## Lessons Learned

- Initial sigma continuity residual reduction is implementable and clean under
  fixed diagnostics, but this approximate vertically uniform divergence
  correction is not beneficial enough for the current incumbent.
- Early MSLP and Z500 improvements did not translate into aggregate primary
  score gains, so future initialization proposals need stronger evidence than
  improving one continuity residual.
- Broader wind or divergence initialization remains risky given this negative
  primary delta and the older severe Helmholtz wind-initialization failure.

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
clean, then continue the loop by asking Researcher for more proposals as
directed by the user.

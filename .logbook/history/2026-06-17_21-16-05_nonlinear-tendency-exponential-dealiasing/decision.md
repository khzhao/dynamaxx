# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: `-1.1182607015496349`
- Iteration candidate primary score: `-1.1431871366924837`
- Iteration incumbent primary score: `-1.143975258592661`
- Iteration delta: `+0.0007881219001772966`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1301883620649706`
- Validation delta: not run

## Rationale

The candidate passed the full test suite, the fast gate, iteration diagnostics,
and all fixed RMSE guardrails, but it failed the fixed iteration promotion
threshold. The iteration primary score improved by
`+0.0007881219001772966`, which is below the required `+0.002`, so validation
was not run.

The guardrails were clean. Day 1-5 mean RMSE improved slightly for every target
variable: `10m_u_component_of_wind`, `2m_temperature`, `geopotential_500`, and
`mean_sea_level_pressure`. No target-variable mean RMSE regression exceeded the
`2%` early-lead threshold, and no individual target variable plus lead RMSE
regression exceeded the `10%` threshold. The worst variable-plus-lead regression
was only `2m_temperature` at `312` hours with `+0.025473847191722303%`.

The candidate is scientifically useful negative evidence rather than an
accepted improvement: nonlinear explicit-tendency dealiasing appears stable and
slightly helpful, but the effect is too small to replace the incumbent under
the current fixed WeatherBench2 gates.

## Lessons Learned

- Applying a conservative exponential modal filter to explicit tendencies is
  not equivalent to prior broad damping failures; it produced clean diagnostics
  and a small positive iteration delta.
- The effect size was below the promotion threshold, so future proposals may
  revisit anti-aliasing only if they introduce a materially stronger mechanism
  than this exact cutoff/order/attenuation configuration.
- Because all guardrails were clean, the limiting issue is aggregate skill gain,
  not early wind, pressure, height, or temperature regression.

## Cleanup Completed

- Candidate code retained or reverted: reverted the eight modified source and
  test files; no rejected code remains in tracked files.
- Research state updated: selected ready proposal was moved into this immutable
  history directory before implementation.
- Leaderboard updated: no; incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
- Git status checked: tracked worktree clean on branch `kzhao--codex`.

## Next Action

Revert the eight candidate implementation files, verify the tracked worktree is
clean, then continue the loop by asking Researcher for more proposals as
directed by the user. The staged `continuity-balanced-divergence-init` idea
remains available for a later triage pass.

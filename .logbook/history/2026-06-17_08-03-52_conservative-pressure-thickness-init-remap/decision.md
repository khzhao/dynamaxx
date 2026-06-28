# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.1507511369682746`
- Iteration incumbent primary score: `-1.143975258592661`
- Iteration delta: `-0.006775878375613553`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1301883620649706`
- Validation delta: not run

## Rationale

The candidate passed the fast gate and produced clean iteration diagnostics, but
it did not meet the fixed iteration promotion threshold. Its iteration primary
score regressed by `-0.006775878375613553`, below the required `+0.002`
minimum, so validation was not run.

Guardrails were clean despite the primary-score regression. The worst early
day 1-5 mean RMSE regression was `geopotential_500` at
`+1.039093269800594%`, below the `2%` limit. The worst variable+lead RMSE
regression was `geopotential_500` at 168 h with `+1.68997781487689%`, below
the `10%` limit. The negative primary delta is sufficient for rejection under
the protocol.

The physical lesson is that interpreting pressure-level analysis channels as
finite layer averages and remapping them conservatively in log-pressure
thickness hurt medium-lead mass-field evolution for this incumbent. The
center-sampled log-pressure initialization plus layer-mean hydrostatic
temperature estimate remains the better initialization contract.

## Lessons Learned

- Conservative layer overlap was stable but degraded primary score, with the
  largest RMSE increases concentrated in `geopotential_500` and
  `mean_sea_level_pressure` around days 4-8.
- The pressure-level WeatherBench inputs likely behave more like useful point
  samples for this adapter than like layer averages for all initialized fields.
- Future initialization proposals should avoid broad remapping of winds and
  thermodynamic fields unless they include a mechanism that preserves resolved
  vertical shear and mass-field phase.

## Cleanup Completed

- Candidate code retained or reverted: reverted; no source/test changes
  retained.
- Research state updated: consumed ready proposal removed after preserving it
  in this history directory.
- Leaderboard updated: no; incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
- Git status checked: completed after rollback.

## Next Action

Continue the optimization loop from the existing incumbent and re-triage the
remaining staged proposals or request new Researcher proposals if needed.

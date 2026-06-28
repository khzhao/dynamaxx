# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-1.143975258592661`
- Iteration incumbent primary score: `-1.1486642287781768`
- Iteration delta: `+0.004688970185515728`
- Validation candidate primary score: `-1.1301883620649706`
- Validation incumbent primary score: `-1.1354942896701432`
- Validation delta: `+0.005305927605172567`

## Rationale

The candidate passed the fixed fast, iteration, and validation gates without
changing evaluation metrics, WeatherBench2 splits, target variables, lead
times, or the deterministic forecast contract. Fast diagnostics were clean.
Iteration primary score improved by `+0.004688970185515728`, above the `+0.002`
promotion threshold. Validation primary score improved by
`+0.005305927605172567`, above the `+0.001` acceptance threshold.

Guardrails passed on both iteration and validation. The worst early day 1-5
mean RMSE regression was `10m_u_component_of_wind`, at
`+0.135177550727686%` on iteration and `+0.1217093125612292%` on validation,
well below the `2%` guardrail. No variable+lead RMSE regression exceeded
`10%`; the largest was `10m_u_component_of_wind` at 24 h, with
`+0.5852716718076152%` on iteration and `+0.5788519865989503%` on validation.

The implementation is a narrow initialization-only refinement of the accepted
hydrostatic-thickness candidate. It replaces point finite-difference
hydrostatic temperature estimates with adjacent-layer hypsometric means, while
preserving DFI, weak Held-Suarez relaxation, near-surface residual correction,
log-pressure pressure-to-sigma initialization, output packing, vertical
advection, zero orography, and all public forecast interfaces.

## Lessons Learned

- Layer-mean hypsometric initialization improved the already strong
  hydrostatic incumbent, suggesting that the accepted point derivative still
  carried removable vertical-noise or endpoint sensitivity.
- The largest regressions shifted to small short-lead `10m_u_component_of_wind`
  movements rather than `2m_temperature`; future initialization proposals
  should track both channels explicitly.
- Exact `model_name` filtering remains mandatory because metric artifacts also
  contain `persistence` rows with duplicate channel and lead keys.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as
  `a7833574e9ade1a5271bd8cbef2fa1357465f5a8`.
- Research state updated: consumed ready proposal removed after preserving it
  in this history directory.
- Leaderboard updated: yes, incumbent set to
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
- Git status checked: tracked worktree clean after commit; ignored logbook and
  evaluation artifacts retained locally.

## Next Action

Start the next continuous-loop iteration from the new incumbent, inspect
resources and research state, then select from staged proposals or request fresh
Researcher proposals if needed.

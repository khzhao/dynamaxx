# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: `-1.1788189813240295`
- Iteration candidate primary score: `-1.199169003293556`
- Iteration incumbent primary score: `-1.143975258592661`
- Iteration delta: `-0.055193744700895`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1301883620649706`
- Validation delta: not run

## Rationale

The candidate passed full tests, fast diagnostics, and iteration diagnostics,
but it failed the fixed iteration promotion gate. The iteration primary score
regressed by `-0.055193744700895`, far below the required `+0.002` promotion
threshold, so validation was not run.

The RMSE guardrails did not fail. The early day 1-5 mean RMSE relative
regression was `+1.1484758515921711%`, below the `2%` limit. The worst
variable+lead regression was `10m_u_component_of_wind` at 24 h with
`+6.446958113464453%`, below the `10%` limit. Diagnostics were clean with
`failed=False` and `issues=0`.

The physical lesson is that bounded moist virtual-temperature dynamics are now
numerically stable under the repaired finite-output incumbent, but they degrade
the fixed WeatherBench2 iteration score substantially. The benchmark remains
sensitive to humidity in diagnostics, but allowing passive humidity to feed
back on rollout mass, wind, and temperature dynamics is not beneficial without
additional moist physics or a stronger mechanism.

## Lessons Learned

- The original fast-failed moist mechanism can now run cleanly after finite
  output repairs and explicit humidity bounds, but clean diagnostics are not
  enough; active moist density feedback regresses aggregate skill.
- The largest guardrail movement was early 10 m zonal wind, consistent with
  moisture-altered pressure gradients perturbing balanced flow.
- Further humidity proposals should not simply activate passive humidity in
  dynamics. They would need new evidence or a separate infrastructure proposal
  for diagnostics, not model-selection tuning.

## Cleanup Completed

- Candidate code retained or reverted: reverted the seven modified source and
  test files; no rejected code remains in tracked files.
- Research state updated: ready proposal removed after this immutable history
  record was completed.
- Leaderboard updated: no; incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
- Git status checked: tracked worktree clean on branch `kzhao--codex`.

## Next Action

Revert the rejected implementation files, clear the consumed ready proposal,
verify a clean tracked worktree, then continue the loop by asking Researcher
for any genuinely new non-duplicate mechanism. If none remain after documented
search and Evaluator confirmation, record the resumed blocker evidence.

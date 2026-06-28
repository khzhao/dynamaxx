# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.1439751141779315`
- Iteration incumbent primary score: `-1.143975258592661`
- Iteration delta: `+1.444147295082132e-07`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1301883620649706`
- Validation delta: not run

## Rationale

The candidate passed full tests, fast sanity, iteration diagnostics, and fixed
RMSE guardrails, but it did not meet the protocol's iteration promotion
threshold. The iteration primary delta was only
`+1.444147295082132e-07`, far below the required `+0.002`, so validation was
not run and the candidate cannot be accepted.

The guardrails were effectively neutral. The maximum early day 1-5 mean RMSE
regression was `3.7026508155931215e-08`, below the `2%` limit. The maximum
variable+lead RMSE regression was `2.126336127121496e-07`, below the `10%`
limit. Diagnostics were clean with `failed=False` and `issues=0`.

The physical lesson is that exact-pole pressure-level wind regularization is
stable but too small to matter under the fixed global WeatherBench2 iteration
metric for this incumbent. The operation changes only two latitude rows before
the spectral wind transform, and the observed score movement is numerical-noise
scale.

## Lessons Learned

- Exact-pole-only vector wind regularization does not materially improve the
  current incumbent, even though it is physically defensible and stable.
- Future wind proposals need a stronger mechanism than coordinate-singular row
  cleanup, but broad wind-control changes remain risky given prior history.
- The remaining research queue is nearly exhausted; the next iteration should
  either revisit the one narrow staged pressure-edge idea or document a blocked
  state after a final Researcher and Evaluator pass.

## Cleanup Completed

- Candidate code retained or reverted: reverted the six implementation source
  and test files; no rejected code remains in tracked files.
- Research state updated: consumed ready proposal removed after preserving an
  immutable copy in this history directory.
- Leaderboard updated: no; incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
- Git status checked: tracked worktree clean on branch `kzhao--codex`.

## Next Action

Start the next continuous-loop iteration by inspecting resources and research
state, then ask the Researcher and Evaluator whether the remaining staged
bounded log-pressure edge extrapolation proposal should become the sole ready
candidate or whether the loop is blocked by exhausted research ideas.

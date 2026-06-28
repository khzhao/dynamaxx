# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.144930302953247`
- Iteration incumbent primary score: `-1.143975258592661`
- Iteration delta: `-0.000955044360586`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1301883620649706`
- Validation delta: not run

## Rationale

The candidate passed full tests, fast sanity, and iteration diagnostics, but it
failed the fixed iteration promotion gate. The primary score regressed by
`-0.000955044360586`, below the required `+0.002` threshold, so validation was
not run.

RMSE guardrails were clean. The largest early day 1-5 mean RMSE regression was
`geopotential_500` at `+0.3660%`, below the `2%` limit. The largest
variable+lead RMSE regression was `mean_sea_level_pressure` at 168 h with
`+1.0107%`, below the `10%` limit. Diagnostics were clean with `failed=False`
and `issues=0`.

The physical lesson is that bounding log-pressure initialization extrapolation
at the pressure-stack edges is stable but not helpful for the current
incumbent. Like the broader rejected pressure-remap candidates, it modestly
hurts mass-field skill, even though it avoids the severe output-path guardrail
failures seen in broader coordinate changes.

## Lessons Learned

- The accepted incumbent's existing finite linear edge extrapolation appears
  preferable to nearest-edge clipping for initialization under the fixed
  iteration metric.
- Additional pressure-coordinate initialization changes need stronger evidence
  before consuming another iteration; edge-only bounded extrapolation was not a
  useful fallback.
- After this rejection, the active research queue has no remaining ready,
  staged, or proposal ideas unless a fresh Researcher search finds a genuinely
  new mechanism.

## Cleanup Completed

- Candidate code retained or reverted: reverted the six modified source/test
  files and removed the candidate-only new test file.
- Research state updated: ready proposal removed after this immutable history
  record was completed.
- Leaderboard updated: no; incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
- Git status checked: tracked worktree clean on branch `kzhao--codex`.

## Next Action

Revert the rejected implementation files, clear the consumed ready proposal,
verify a clean tracked worktree, then start the next continuous-loop pass. If
Researcher and Evaluator cannot identify another non-duplicate, researchable
idea, document the protocol stop condition for exhausted ideas.

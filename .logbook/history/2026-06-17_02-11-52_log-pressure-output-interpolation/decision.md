# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.2138808205324492`
- Iteration incumbent primary score: `-1.2155220438349765`
- Iteration delta: `+0.0016412233025273615`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.2028991078287248`
- Validation delta: not run

## Rationale

The candidate passed the fast sanity gate and produced clean iteration
diagnostics, but it did not meet the fixed iteration promotion gate. The
iteration primary delta was `+0.0016412233025273615`, below the required
`+0.002` threshold. The early mean RMSE day-1-through-day-5 guardrail passed,
but 54 variable+lead RMSE regressions exceeded the 10% guardrail threshold.
The largest failures were in 2 m temperature at medium leads, with relative
regressions above 200%.

Validation was correctly skipped because iteration promotion failed. The
candidate cannot become incumbent under the fixed protocol.

## Lessons Learned

- Output-only log-pressure remapping can improve aggregate primary score
  slightly while badly redistributing variable+lead RMSE errors.
- The accepted log-pressure initialization improvement should not be generalized
  automatically to output diagnostics; the output path has different metric and
  residual-correction interactions.
- Future output-remap proposals need stronger variable-specific evidence before
  spending a full iteration run.

## Cleanup Completed

- Candidate code retained or reverted: reverted after preserving this history
  record.
- Research state updated: selected ready proposal copied into this immutable
  history directory; ready copy removed after rejection.
- Leaderboard updated: no, incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init`.
- Git status checked: yes, tracked worktree clean after rollback.

## Next Action

Start the next continuous-loop iteration with
`dinosaur_dfi_surface_residual_weak_hs_logp_init` still as incumbent.

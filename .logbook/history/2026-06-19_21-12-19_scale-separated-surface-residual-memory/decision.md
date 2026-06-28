# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.532053269893688`
- Iteration incumbent primary score: `-0.5719873627530224`
- Iteration delta: `+0.03993409285933447`
- Validation candidate primary score: `-0.5219023378614627`
- Validation incumbent primary score: `-0.562579968224105`
- Validation delta: `+0.04067763036264238`

## Rationale

The candidate passed all fixed gates. Unit tests and focused tests passed in
the implementation phase; fast, iteration, and validation completed with clean
diagnostics. Iteration exceeded the `+0.002` promotion threshold, and validation
exceeded the `+0.001` acceptance threshold.

No guardrail blocked acceptance. On iteration and validation, no early day 1-5
target-variable mean RMSE regression exceeded `2%`, and no variable+lead RMSE
regression exceeded `10%`.

The incumbent was not rerun. The cached leaderboard artifacts were used because
they were present, finite, and comparable under the fixed protocol. Candidate
source edits do not invalidate the accepted incumbent cache.

## Lessons Learned

- Scale-separating near-surface residual memory is a high-value output-only
  correction for the current incumbent.
- The useful signal is broad and stable enough to pass validation, not just the
  iteration scratchpad.
- Cached incumbent metrics should remain the default comparison path unless a
  concrete cache invalidation is found.

## Cleanup Completed

- Candidate code retained or reverted: retained for commit.
- Research state updated: selected proposal is preserved in this immutable
  history directory.
- Leaderboard updated: yes, updated to the accepted candidate and candidate
  iteration/validation artifacts.
- Git status checked: tracked worktree clean after commit.

## Next Action

Commit the accepted source/test changes, then start the next continuous-loop
iteration from the new incumbent.

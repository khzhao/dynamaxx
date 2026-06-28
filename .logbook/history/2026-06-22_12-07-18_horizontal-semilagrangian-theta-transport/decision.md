# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.32000443139324114`
- Iteration incumbent primary score: `-0.42701187536092744`
- Iteration delta: `+0.1070074439676863`
- Validation candidate primary score: `-0.31443387067049233`
- Validation incumbent primary score: `-0.417391902036791`
- Validation delta: `+0.10295803136629866`

## Rationale

The candidate passed all fixed model-selection gates against the cached
leaderboard incumbent artifacts. Incumbent iteration and validation metrics were
reused from valid leaderboard cache artifacts; no incumbent evaluation was
rerun.

Fast diagnostics were clean. Iteration exceeded the `+0.002` promotion
threshold by a wide margin, and validation exceeded the `+0.001` acceptance
threshold. Diagnostics were clean for fast, iteration, and validation. Early
day 1-5 mean RMSE guardrails passed for every target variable. The worst
variable-lead RMSE regressions were negative on both iteration and validation,
so the candidate reduced RMSE relative to the incumbent on the measured
guardrail comparisons.

The implementation is side-by-side under the short alias `dino_hsl_theta`, keeps
the forecast contract unchanged, preserves incumbent momentum, vertical
transport, DFI, weak-HS forcing, residuals, and ocean bulk sensible heat flux,
and adds a bounded finite-fallback horizontal semi-Lagrangian theta anomaly
transport path.

## Lessons Learned

- Horizontal theta transport is a high-signal remaining error source for the
  accepted ocean-bulk incumbent.
- A short model alias avoided the long-filename artifact issue seen in earlier
  accepted candidates.
- Cache reuse worked as intended: the incumbent comparison came from valid
  leaderboard artifacts, not from a redundant incumbent run.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as
  `34d20a0afd7133cba41c595072b5c14c8e42a88f`.
- Research state updated: selected ready proposal removed after acceptance.
- Leaderboard updated: yes, to `dino_hsl_theta` and its fixed eval artifact
  paths.
- Git status checked: tracked worktree clean after commit.

## Next Action

Start the next continuous-loop iteration immediately.

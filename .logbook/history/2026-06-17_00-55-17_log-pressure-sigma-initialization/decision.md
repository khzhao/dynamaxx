# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-1.2155220438349765`
- Iteration incumbent primary score: `-1.2218408656785489`
- Iteration delta: `+0.006318821843572353`
- Validation candidate primary score: `-1.2028991078287248`
- Validation incumbent primary score: `-1.2103467803549615`
- Validation delta: `+0.007447672526236682`

## Rationale

The candidate passed all fixed gates. Fast diagnostics were clean with zero
issues. Iteration primary score improved by `+0.006318821843572353`, exceeding
the `+0.002` promotion threshold. Validation primary score improved by
`+0.007447672526236682`, exceeding the `+0.001` acceptance threshold. Candidate
iteration and validation diagnostics were clean, no early mean RMSE regression
exceeded 2%, and no variable+lead RMSE regression exceeded 10%.

The implementation is physically bounded and side-by-side: it changes only the
pressure-coordinate used for pressure-level to sigma initialization and leaves
the incumbent forecast contract, output interpolation, fixed metrics, target
variables, lead times, and evaluation splits unchanged.

## Lessons Learned

- Log-pressure initialization produced a real primary-score improvement while
  RMSE guardrail differences stayed near numerical roundoff, so primary
  improvements may be coming through non-RMSE score components or aggregate
  distributional effects.
- Small initialization-only perturbations can outperform broader pressure-grid
  and forcing changes when they preserve the accepted forecast trajectory and
  output path.
- Future scoring helper snippets should use the existing `dycore_model_names`
  registry helper and avoid speculative protocol helper names.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as
  `bc39a2b7fbbe5fbab0aa568afcf90c32b7a4b41c`.
- Research state updated: selected ready proposal copied into this immutable
  history directory; ready copy removed after acceptance.
- Leaderboard updated: yes, new incumbent is
  `dinosaur_dfi_surface_residual_weak_hs_logp_init`.
- Git status checked: yes, tracked worktree clean after commit.

## Next Action

Start the next continuous-loop iteration with
`dinosaur_dfi_surface_residual_weak_hs_logp_init` as the incumbent.

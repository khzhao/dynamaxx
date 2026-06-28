# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.2201311388680774`
- Iteration incumbent primary score: `-0.2197104515448394`
- Iteration delta: `-0.00042068732323799485`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.21940899263836755`
- Validation delta: not applicable

## Rationale

The candidate failed the fixed iteration promotion gate. Its iteration primary
score was worse than the cached incumbent by `-0.00042068732323799485`, below
the required `+0.002` promotion threshold. Candidate fast and iteration
diagnostics were clean, but clean diagnostics are not sufficient for promotion.

The fixed RMSE guardrails passed. The largest early day 1-5 mean RMSE
regression was `geopotential_500` at `+6.191927952562836e-07`, far below the
`2%` threshold. The worst variable+lead RMSE regression was
`geopotential_500` at 336h with `+0.0015971997064777059`, below the `10%`
threshold.

The proposal's early no-op claim was effectively confirmed: leads through 120h
were incumbent-equivalent by RMSE, with maximum absolute relative movement
`3.412585971358586e-06`. The negative primary delta therefore indicates that
relaxing the accepted vertical-DSE cap after day 5 did not recover useful
late-lead signal under the fixed iteration split.

The incumbent iteration metrics were reused from the leaderboard cache and no
incumbent rerun was performed. Validation and golden were not run because
iteration did not promote.

## Lessons Learned

- The accepted `0.05 K` vertical-DSE per-step cap is not obviously suppressing
  useful late-lead signal; widening it to `0.08 K` after 120h slightly worsened
  the primary score.
- The fixed schedule successfully protected early leads, so the rejection is
  about late-lead utility rather than early guardrail damage.
- Future vertical-DSE refinements should prefer mechanisms that change where
  the increment acts or how imbalance is guarded, rather than simply widening
  the late limiter.

## Cleanup Completed

- Candidate code retained or reverted: reverted from `candidate.diff`; tracked
  source and test files returned to the incumbent state.
- Research state updated: removed
  `.logbook/research/ready/late-lead-vertical-dse-cap-release.md`.
- Leaderboard updated: not updated because the candidate was rejected.
- Git status checked: tracked worktree clean; pre-existing untracked `gifs/`
  directory preserved.

## Next Action

Continue the optimization loop with `dino_hsl2_mass_dse_wtg_vdse_ramp` as the
incumbent.

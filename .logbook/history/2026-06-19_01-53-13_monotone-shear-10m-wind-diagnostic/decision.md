# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.8309040873499036`
- Iteration incumbent primary score: `-0.8308832822743712`
- Iteration delta: `-0.000020805075532370765`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.8148379476593253`
- Validation delta: not run

## Rationale

The candidate failed the fixed iteration promotion gate. Its primary score delta
was slightly negative and below the required `+0.002` threshold, so validation
was not run.

Fast and iteration diagnostics were clean. The early day 1-5 aggregate RMSE
changed by only `+0.000040200774984299765%`, far below the `+2%` guardrail.
The largest variable-by-lead RMSE regression was `geopotential_500` day 12 at
`+0.009725953842613903%`, far below the `+10%` guardrail. The implementation
was stable, but the monotone scalar cap did not materially improve the scored
10 m wind behavior or the aggregate primary score.

The incumbent iteration metrics were reused from `.logbook/leaderboard.json`
under the updated Scorer cache-reuse rule. Reuse checks passed because the
requested incumbent matched the leaderboard incumbent, cached artifacts were
readable with finite scores, the fixed fingerprint matched, committed eval and
registry code were unchanged relative to the cached eval commit, no
uncommitted eval-code changes existed, and the candidate was side-by-side with
the incumbent monotone option disabled.

## Lessons Learned

- The late `10m_u_component_of_wind` regression from theta recentering is not
  primarily fixed by a conservative monotone scalar speed cap.
- Output-only wind follow-ups need a stronger physical diagnostic than limiting
  the existing Richardson factor to move the fixed primary score.
- Cached incumbent metrics can safely reduce scoring cost when the explicit
  reuse checks pass; this iteration compared a fresh candidate iteration
  against valid cached incumbent iteration artifacts.

## Cleanup Completed

- Candidate code retained or reverted: reverted. No tracked source or test
  changes from this rejected candidate should remain after rollback.
- Research state updated: proposal, implementation, scores, scoring notes,
  decision, and artifact manifest are recorded under
  `.logbook/history/2026-06-19_01-53-13_monotone-shear-10m-wind-diagnostic/`.
- Leaderboard updated: no. The incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter`.
- Git status checked: tracked worktree clean after rollback.

## Next Action

Start the next iteration immediately. The user explicitly removed idea
exhaustion as a stop condition, so the Researcher must continue producing new
ideas without end unless paused by the user or blocked by infrastructure.

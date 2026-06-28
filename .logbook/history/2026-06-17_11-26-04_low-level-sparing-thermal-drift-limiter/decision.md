# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.1454928597212104`
- Iteration incumbent primary score: `-1.143975258592661`
- Iteration delta: `-0.001517601128549373`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-1.1301883620649706`
- Validation delta: not run

## Rationale

The candidate passed focused implementation checks, full pytest, fast sanity,
and iteration diagnostics, but it failed the fixed iteration promotion gate.
The iteration primary delta was negative (`-0.001517601128549373`) versus the
required `+0.002`, so validation was not run.

The guardrails were clean. The largest early day 1-5 mean RMSE regression was
`geopotential_500` at `+0.108127%`, below the 2% limit. The largest single
variable+lead RMSE regression was `10m_u_component_of_wind` at 144h with
`+0.217026%`, below the 10% limit. The low-level-sparing limiter avoided the
prior full-column thermal recentering wind guardrail failure, but it also lost
the positive primary-score signal that motivated the follow-up.

## Lessons Learned

- Sparing lower sigma layers protects the early `10m_u_component_of_wind`
  guardrail, but the upper/mid zero-mode limiter does not improve this
  incumbent's aggregate iteration skill.
- The earlier full-column thermal recentering benefit likely depended on a
  broader thermal-state intervention, including lower layers or balanced
  momentum coupling, and cannot be recovered by freezing only upper/mid layer
  means.
- Future thermal-drift proposals should not repeat simple zero-mode freezing
  masks without a stronger balanced-dynamics mechanism.

## Cleanup Completed

- Candidate code retained or reverted: reverted the candidate source and test
  changes from the six touched files.
- Research state updated: ready proposal removed after the immutable history
  record was completed.
- Leaderboard updated: no; incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init`.
- Git status checked: tracked worktree clean on branch `kzhao--codex`.

## Next Action

Revert the candidate implementation changes, remove the active ready proposal,
verify tracked worktree cleanliness, then continue the optimization loop with
the staged research queue.

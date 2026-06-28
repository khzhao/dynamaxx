# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.34541538912978986`
- Iteration incumbent primary score: `-0.2197104515448394`
- Iteration delta: `-0.12570493758495047`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.21940899263836755`
- Validation delta: not applicable

## Rationale

The candidate failed the fixed iteration promotion gate. Its iteration primary
score was worse than the cached incumbent by `-0.12570493758495047`, far below
the required `+0.002` promotion threshold. Candidate fast and iteration
diagnostics were clean, but the primary score and guardrails clearly rejected
the mechanism.

The early day 1-5 mean RMSE guardrail failed for all four target variables.
The worst early mean regression was `2m_temperature` at
`+10.979379145671885%`, above the fixed `2%` threshold. The worst
variable+lead guardrail also failed: `2m_temperature` at 144h regressed by
`+19.11223950551435%`, above the fixed `10%` threshold.

The incumbent iteration metrics were reused from the leaderboard cache and no
incumbent rerun was performed. Validation and golden were not run because
iteration did not promote.

## Lessons Learned

- Gating the column-mean component of the accepted vertical-DSE increment by a
  local hydrostatic-work ratio removed or distorted a component that is needed
  for the incumbent's skill.
- The damage was broad in early-lead RMSE and especially severe for
  `2m_temperature`, so future vertical-DSE spatial gates should be treated as
  high risk unless they are much weaker or act on a narrower, physically
  isolated subset.
- The fast-score anomaly was directionally useful: the candidate's very poor
  fast score anticipated the severe fixed iteration failure even though fast is
  not an acceptance gate.

## Cleanup Completed

- Candidate code retained or reverted: reverted from `candidate.diff`; tracked
  source and test files returned to the incumbent state.
- Research state updated: removed
  `.logbook/research/ready/hydrostatic-work-gated-vertical-dse.md`.
- Leaderboard updated: not updated because the candidate was rejected.
- Git status checked: tracked worktree clean; pre-existing untracked `gifs/`
  directory preserved.

## Next Action

Continue the optimization loop with `dino_hsl2_mass_dse_wtg_vdse_ramp` as the
incumbent.

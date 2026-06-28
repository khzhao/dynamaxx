# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.29185769674400885`
- Iteration incumbent primary score: `-0.2616483974683927`
- Iteration delta: `-0.030209299275616164`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.2600180396322455`
- Validation delta: not applicable

## Rationale

The candidate failed the fixed iteration promotion threshold. It needed an
iteration delta of at least `+0.002` against the cached incumbent
`dino_hsl2_mass_dse`, but measured `-0.030209299275616164`. Candidate fast and
iteration diagnostics were clean, and the incumbent iteration and validation
caches were valid and reused from `.logbook/leaderboard.json`; no incumbent
rerun was needed.

The early RMSE guardrail also failed. Mean sea level pressure regressed by
`2.4455573339468595%` over lead days 1-5, exceeding the `2%` limit. The worst
variable+lead RMSE guardrail passed, with mean sea level pressure at 360 hours
regressing by `7.026815500932039%`, below the `10%` limit. Rejection is driven
by both broad primary-score degradation and early MSLP guardrail failure.

Validation and golden were not run because iteration did not promote.

## Lessons Learned

- Hydrostatic inversion of the mass-DSE horizontal tendency is too aggressive
  for the current sigma-core balance and damages early pressure skill.
- The accepted `1 / Cp` conversion remains better empirical behavior for the
  current incumbent than a direct `(Cp I + G_sigma)` inversion.

## Cleanup Completed

- Candidate code retained or reverted: reverted with the saved candidate diff.
- Research state updated: removed `.logbook/research/ready/hydrostatic-inverted-mass-dse-hsl.md`.
- Leaderboard updated: not updated because the candidate was rejected.
- Git status checked: tracked tree clean after rollback; unrelated untracked
  `gifs/` directory preserved.

## Next Action

Continue the optimization loop with the next research/evaluation iteration.

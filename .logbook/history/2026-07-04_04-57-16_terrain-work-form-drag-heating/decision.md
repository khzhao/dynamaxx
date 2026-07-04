# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.12618112079830215`
- Iteration incumbent primary score: `-0.1285119843716688`
- Iteration delta: `+0.0023308635733666483`
- Validation candidate primary score: `-0.12682079599872897`
- Validation incumbent primary score: `-0.12911217353049617`
- Validation delta: `+0.002291377531767197`

## Rationale

The candidate passed all fixed gates against the cached incumbent artifacts.
Fast, iteration, and validation diagnostics were clean with `failed=false` and
zero issues. The iteration primary delta was above the `+0.002` promotion
threshold, and the validation primary delta was above the `+0.001` acceptance
threshold.

All guardrails passed. Early lead 1-5 mean RMSE regressions over `2%` were zero
on both iteration and validation. Per-variable/lead RMSE regressions over `10%`
were zero on both iteration and validation. The worst validation per-lead RMSE
comparison was `2m_temperature` at day 1 with `-0.004865868217503287%`, which
is an improvement rather than a regression.

Incumbent iteration and validation metrics were reused from
`.logbook/leaderboard.json` after cache-validity checks. No incumbent or golden
evaluation was run.

## Lessons Learned

- The terrain-work form-drag plus local heat-return mechanism produced a
  repeatable positive signal on both iteration and validation while improving
  all fixed guardrail comparisons.
- The accepted lower-column orographic-lift terrain-work diagnostic is a useful
  hook for momentum processes, not just thermal terrain-lift increments.
- Future terrain-drag proposals should preserve conservative caps and avoid new
  static-data infrastructure unless a separate infrastructure proposal is
  reviewed first.
- Scoring helpers must compare only rows matching the result model name because
  evaluator artifacts also contain persistence rows.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as
  `8f0b4f529d29d372341e136bd11cbe2f21542bc2`.
- Research state updated: ready proposal removed; accepted history record
  retained.
- Leaderboard updated: yes, to `dino_ri2m_ekman_depth_orolift_lwind_twork_drag`.
- Git status checked: source/test changes committed; pre-existing untracked
  `gifs/` left untouched.

## Next Action

Continue the optimization loop from the new incumbent
`dino_ri2m_ekman_depth_orolift_lwind_twork_drag`.

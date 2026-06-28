# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.25851235493825614`
- Iteration incumbent primary score: `-0.2616483974683927`
- Iteration delta: `+0.0031360425301365513`
- Validation candidate primary score: `-0.25704033104116597`
- Validation incumbent primary score: `-0.2600180396322455`
- Validation delta: `+0.002977708591079542`

## Rationale

The candidate passed full repository tests, fast diagnostics, iteration, and
validation. Iteration exceeded the `+0.002` promotion threshold and validation
exceeded the `+0.001` acceptance threshold. Candidate fast, iteration, and
validation diagnostics were clean with `failed=False` and `issues=0`.

The fixed RMSE guardrails were clean. Early-lead mean RMSE changes were neutral
or favorable for all target variables in both iteration and validation. The
worst single-lead RMSE regressions were tiny `geopotential_500` day-1 changes:
`+0.023163%` on iteration and `+0.020035%` on validation, far below the `10%`
guardrail.

The Scorer reused cached incumbent iteration and validation metrics from
`.logbook/leaderboard.json` after validating cache compatibility. No incumbent
rerun occurred. Golden was not run.

## Lessons Learned

- A bounded tropical WTG mass-DSE thermal relaxation produced score-scale
  gains on both iteration and validation without destabilizing diagnostics or
  guardrails.
- The strongest early-lead relative improvements were in
  `10m_u_component_of_wind` and `mean_sea_level_pressure`, suggesting the
  tropical thermal balance term improves downstream mass and wind evolution.
- Future related proposals should preserve the positive-time-only, thermally
  bounded, layer-neutral shape while testing whether the WTG mechanism can be
  made cheaper or slightly stronger without disturbing day-1 Z500.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as
  `d8561caebb78ca096263d8c412217570ff2d1f46`.
- Research state updated: selected ready proposal removed after acceptance.
- Leaderboard updated: yes, ignored logbook pointer now references
  `dino_hsl2_mass_dse_wtg` and the accepted commit hash.
- Git status checked: tracked worktree clean; unrelated untracked `gifs/`
  directory preserved.

## Next Action

Continue the optimization loop with the next Researcher/Evaluator cycle.

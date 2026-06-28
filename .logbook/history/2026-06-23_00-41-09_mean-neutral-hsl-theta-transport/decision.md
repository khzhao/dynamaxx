# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.31273598260124896`
- Iteration incumbent primary score: `-0.31282890543336245`
- Iteration delta: `+0.00009292283211348451`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.3072374345999185`
- Validation delta: not run

## Rationale

`dino_hsl_mean` passed the fast and iteration execution gates with clean
diagnostics, but it failed the fixed iteration promotion gate. The primary
iteration delta versus cached incumbent `dino_hsl2_theta` was positive but only
`+0.00009292283211348451`, below the required `+0.002` improvement threshold.
Validation was therefore correctly skipped.

The guardrails did not force rejection by themselves. Early day 1-5 mean RMSE
improved for `2m_temperature`, `geopotential_500`, and
`mean_sea_level_pressure`, with a small `10m_u_component_of_wind` regression of
`+0.00027903216842606327` RMSE. The worst variable+lead RMSE regression was
`geopotential_500` at `216` hours with absolute RMSE delta
`+0.06995778581313061`, well below the fixed 10% guardrail. The candidate was
stable, but the primary-score movement was too small to justify validation.

Incumbent iteration metrics were reused from the valid leaderboard cache:
`outputs/eval/iteration_dino_hsl2_theta.json` and
`outputs/eval/iteration_dino_hsl2_theta.csv`. The incumbent was not rerun.

## Lessons Learned

- Removing layerwise HSL theta remap zero modes is stable and slightly helpful
  on the iteration primary score, but not enough to beat the incumbent under
  the fixed promotion threshold.
- The accepted `dino_hsl2_theta` balance appears sensitive to small theta
  transport changes; conservation refinements should target larger coupled
  benefits before consuming validation compute.
- Future HSL theta work should avoid additional low-amplitude refinements
  unless paired with a stronger physical mechanism and bounded implementation.

## Cleanup Completed

- Candidate code retained or reverted: reverted after saving `candidate.diff`.
- Research state updated: ready proposal removed after terminal decision.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: yes, after rollback.

## Next Action

Continue the optimization loop with the next Researcher/Evaluator cycle or a
fresh triage of staged ideas, selecting exactly one ready proposal.

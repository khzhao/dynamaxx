# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.2801194788322577`
- Iteration incumbent primary score: `-0.2616483974683927`
- Iteration delta: `-0.018471081363864994`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.2600180396322455`
- Validation delta: not applicable

## Rationale

The candidate completed full unit tests, fast, and iteration with clean
diagnostics, but failed the fixed iteration promotion gate by a large margin.
The cached incumbent iteration artifact for `dino_hsl2_mass_dse` was valid and
was reused; no incumbent rerun was warranted. Candidate iteration scored
`-0.2801194788322577`, which is `-0.018471081363864994` below the cached
incumbent score and well below the required `+0.002` improvement.

The fixed RMSE guardrails also failed. Early day-1-to-5 mean `2m_temperature`
RMSE regressed by `+37.99203594077941%`, above the `2%` limit. Individual
variable-lead regressions above `10%` occurred 26 times, concentrated in
`2m_temperature` and `mean_sea_level_pressure`; the largest reported failures
were `2m_temperature` at 240 hours with `+120.01798535077835%` RMSE regression
and `mean_sea_level_pressure` at 240 hours with `+34.46242560069296%`.

Validation was skipped because the iteration promotion gate failed. Golden was
not run.

## Lessons Learned

- Redistributing the accepted ocean heat-flux increment through lower sigma
  layers is numerically stable but materially harms the aggregate score.
- The accepted lowest-layer ocean heat-flux placement appears important for
  preserving the current `2m_temperature` skill.
- Future ocean-forcing proposals should not deepen the heat source without a
  stronger constraint protecting screen-temperature error.

## Cleanup Completed

- Candidate code retained or reverted: reverted using
  `.logbook/history/2026-06-24_12-01-01_distributed-ocean-heat-flux/candidate.diff`
- Research state updated: removed
  `.logbook/research/ready/distributed-ocean-heat-flux.md`
- Leaderboard updated: no, rejected candidate
- Git status checked: tracked files clean; pre-existing untracked `gifs/`
  directory preserved

## Next Action

Start the next continuous-loop iteration by generating and triaging new
Researcher proposals against the cached `dino_hsl2_mass_dse` incumbent.

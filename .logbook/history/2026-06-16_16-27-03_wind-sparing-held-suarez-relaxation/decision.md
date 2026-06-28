# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: -1.2218408656785489
- Iteration incumbent primary score: -1.2854136202685928
- Iteration delta: 0.06357275459004397
- Validation candidate primary score: -1.2103467803549615
- Validation incumbent primary score: -1.2725740410982802
- Validation delta: 0.062227260743318746

## Rationale

The candidate passed the fixed fast, iteration, and validation gates without
running golden. The iteration primary delta exceeded the required `+0.002`
threshold, and the validation primary delta exceeded the required `+0.001`
threshold. Candidate diagnostics were clean for fast, iteration, and
validation.

The early day 1-5 mean RMSE guardrail passed for all evaluated variables on
both splits. The variable+lead RMSE guardrail also passed for all evaluated
variables on both splits. The largest validation regression was 10 m zonal wind
at 360 hours with relative regression `0.08252957396916741`, below the 10
percent limit.

The mechanism is physically plausible for this dycore selection round because
it adds weak thermal relaxation while preserving the accepted DFI and
near-surface residual diagnostics. It does not change the forecast contract,
the deterministic gates, the target variables, the splits, or the metrics.

## Lessons Learned

- Weak thermal Held-Suarez relaxation improves primary score on both fixed
  selection splits while keeping diagnostics clean.
- The largest cost is in long-lead 10 m wind, so future proposals should avoid
  spending more of that guardrail margin without a compensating broad score
  gain.
- Exact model-name filtering is required when reading evaluation JSON files
  because persistence rows are present beside candidate rows.

## Cleanup Completed

- Candidate code retained or reverted: retained in commit `4756cc9a4b69c41eec60e2177fb03a73974f0e2d`
- Research state updated: ready proposal removed after acceptance
- Leaderboard updated: yes
- Git status checked: tracked status clean after acceptance commit; final clean check recorded by orchestrator

## Next Action

Start the next optimization iteration from
`dinosaur_dfi_surface_residual_weak_hs` as the incumbent.

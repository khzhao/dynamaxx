# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.21983337873577272
- Iteration incumbent primary score: -0.2197104515448394
- Iteration delta: -0.0001229271909333196
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.21940899263836755 cached, not used for this decision
- Validation delta: not run

## Rationale

The candidate passed the local and fast sanity gates: `uv run pytest` completed with 261 passed and 2 skipped, and candidate `fast` reported `failed=false`, zero issues, 120 records, and primary score `-0.22392494621838646`.

The fixed candidate iteration gate also completed cleanly, with `failed=false`, zero diagnostic issues, and 120 records. The incumbent was not rerun; the Scorer reused the valid cached incumbent iteration artifacts from `.logbook/leaderboard.json`.

The candidate did not meet the iteration promotion gate. Its primary score was `-0.21983337873577272` versus cached incumbent `-0.2197104515448394`, a signed delta of `-0.0001229271909333196`, below the required `+0.002` threshold. Validation was therefore skipped under protocol.

Guardrails were clean but did not rescue the candidate. The worst early day-1-through-day-5 mean RMSE relative regression was `geopotential_500` at `+1.7699136834368657e-07`, below the `+0.02` threshold. The worst variable+lead RMSE relative regression was `10m_u_component_of_wind` at 360 h, `+0.0008113386118853491`, below the `+0.10` threshold.

## Lessons Learned

- Weakening the accepted tropical WTG mass-DSE relaxation after day 5 did not improve the fixed iteration score.
- The very small guardrail movement suggests the taper was numerically stable but did not address a primary-score bottleneck.
- The accepted incumbent's fixed-strength WTG relaxation remains preferable under the current protocol.

## Cleanup Completed

- Candidate code retained or reverted: reverted after this decision record was written.
- Research state updated: ready proposal removed after copying it into this history directory.
- Leaderboard updated: no, rejected candidates do not update the leaderboard.
- Git status checked: yes, after cleanup.

## Next Action

Continue the optimization loop with a new Researcher/Evaluator pass and select exactly one ready proposal for the next implementation.

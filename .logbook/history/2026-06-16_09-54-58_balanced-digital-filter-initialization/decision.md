# Decision Record

## Decision

`accepted`

## Score Summary

- Fast candidate primary score: -1.2844866682514346
- Fast diagnostics: passed, issue count 0
- Iteration candidate primary score: -1.3208025947740873
- Iteration incumbent primary score: -1.3251884351511753
- Iteration delta: +0.004385840377088002
- Validation candidate primary score: -1.308334010223954
- Validation incumbent primary score: -1.3128324262513928
- Validation delta: +0.004498416027438834

## Rationale

The candidate passed the required fast diagnostic gate with no nonfinite or diagnostic issues. It exceeded the iteration promotion threshold by improving primary score by `+0.004385840377088002`, above the required `+0.002`, while preserving clean diagnostics and passing RMSE guardrails. It then exceeded the validation acceptance threshold by improving primary score by `+0.004498416027438834`, above the required `+0.001`, again with clean diagnostics and no early-lead RMSE guardrail failure.

The mechanism is physically plausible for this adapter because it damps high-frequency initialization imbalance introduced by pressure-level analysis conversion into the sigma-coordinate spectral state. The implementation keeps the forecast contract and fixed evaluation protocol unchanged by registering a side-by-side `dinosaur_dfi` candidate rather than replacing canonical `dinosaur`.

## Lessons Learned

- The accepted finite-output baseline made it possible to distinguish model skill movement from diagnostic failure.
- Digital filter initialization produced a measurable fixed-protocol gain even though the checked target-variable RMSE differences were small; future analysis should inspect primary-score components before assuming where the gain entered.
- Side-by-side registry candidates are useful for keeping incumbent artifacts comparable during model-selection experiments.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as `cfdc344723cee1f267b892ddd924fc5d07b89f2d`.
- Research state updated: removed from `.logbook/research/ready`; immutable copy retained in this history directory.
- Leaderboard updated: yes, incumbent pointer now references `dinosaur_dfi`.
- Git status checked: clean tracked worktree after commit.

## Next Action

Continue the loop by re-triaging the remaining staged proposals against the accepted `dinosaur_dfi` incumbent. Do not run `golden`.

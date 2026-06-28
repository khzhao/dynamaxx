# Decision Record

## Decision

`accepted`

## Score Summary

- Fast candidate primary score: -1.2882176100657747
- Fast diagnostics: passed, issue count 0
- Iteration candidate primary score: -1.3251884351511753
- Iteration incumbent primary score: -1.3251884351511753
- Iteration delta: 0.0, bookkeeping only for same-model infrastructure repair
- Validation candidate primary score: -1.3128324262513928
- Validation incumbent primary score: -1.3128324262513928
- Validation delta: 0.0, bookkeeping only for same-model infrastructure repair

## Rationale

The pre-repair canonical `dinosaur` fast artifact failed fixed diagnostics with `nonfinite_forecast`, making model-selection experiments ambiguous. This repair keeps the forecast contract and fixed evaluation protocols unchanged while making pressure-level output packing finite for out-of-column diagnostic levels.

After the repair, canonical `dinosaur` passed fast, iteration, and validation with zero diagnostic issues and finite metric artifacts. Model-selection delta thresholds were not applied because candidate and incumbent are the same repaired canonical model. Acceptance is based on establishing a finite infrastructure baseline required before further dycore model-selection experiments.

## Lessons Learned

- The fast-gate failure observed for the rejected moist-dynamics candidate was also present in the dry incumbent, so future candidate failures must be interpreted against the repaired finite baseline.
- Pressure-level output diagnostics need explicit below-surface behavior when sigma-coordinate dycore states are emitted on WeatherBench pressure levels.
- Further model-selection proposals can now be evaluated against finite fast, iteration, and validation artifacts for `dinosaur`.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as `4beb6c221f8655f80b6530713ffc75697e9c654e`.
- Research state updated: removed from `.logbook/research/ready`; immutable copy retained in this history directory.
- Leaderboard updated: yes, as a finite baseline pointer for incumbent `dinosaur`.
- Git status checked: clean tracked worktree after commit, branch ahead by 1 commit.

## Next Action

Continue the loop by re-triaging staged model-selection ideas against the accepted finite `dinosaur` baseline. Do not run `golden`.

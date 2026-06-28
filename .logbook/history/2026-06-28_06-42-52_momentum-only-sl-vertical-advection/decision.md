# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.7976931348623157e+308`
- Iteration incumbent primary score: `-0.21299732605547173`
- Iteration delta: `-1.7976931348623157e+308`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.21274255459898536`
- Validation delta: not run

## Rationale

The candidate passed local tests and the fast split, but failed the fixed iteration evaluation. The iteration diagnostics reported 153 issues: 152 non-finite forecast issues and 1 non-finite metric-record issue. That forced the primary score to the failure sentinel and failed the promotion gate before validation.

The incumbent comparison reused valid cached incumbent artifacts from `.logbook/leaderboard.json` at commit `3992244f20b2a938fdd96f8904f3749f5505670d`; no incumbent rerun was needed or performed. Because the candidate did not beat the cached incumbent iteration score and was numerically unstable, it is rejected without validation.

## Lessons Learned

- Momentum-only semi-Lagrangian vertical advection is not stable in this narrow form over the fixed iteration split.
- Future vertical-transport ideas should include stronger full-rollout boundedness checks before full scoring.
- Cached incumbent artifacts are sufficient for comparison when they match the latest accepted commit and fixed protocols.

## Cleanup Completed

- Candidate code retained or reverted: reverted after writing this history record.
- Research state updated: ready proposal moved into this history directory.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: yes, after rollback.

## Next Action

Continue the loop by inspecting resources and git state, then start the next Researcher/Evaluator proposal cycle. There is no protocol stop condition here.

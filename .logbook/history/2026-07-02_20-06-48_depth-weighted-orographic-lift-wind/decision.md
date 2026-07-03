# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.1285119843716688`
- Iteration incumbent primary score: `-0.13156559713631472`
- Iteration delta: `+0.0030536127646459132`
- Validation candidate primary score: `-0.12911217353049617`
- Validation incumbent primary score: `-0.13341144990707632`
- Validation delta: `+0.004299276376580147`

## Rationale

The candidate passed all fixed gates under `roles/PROTOCOL.md`. Full pytest passed with `294 passed, 2 skipped`; candidate fast, iteration, and validation evaluations completed with clean diagnostics. The iteration delta exceeded the `+0.002` promotion threshold, and the validation delta exceeded the `+0.001` acceptance threshold. Early day-1-to-5 RMSE guardrail violations over 2 percent were `0` on iteration and validation, and per-variable/lead RMSE guardrail violations over 10 percent were `0` on both protocols. Cached incumbent metrics were reused after fingerprint and artifact checks; no incumbent or golden evaluation was run.

## Lessons Learned

- Replacing the single lowest terrain-lift wind with a conservative lower-column wind estimate is a stronger orographic-lift refinement than operator-order changes.
- The gain came with essentially neutral RMSE guardrails, suggesting the mechanism improved aggregate score without broad degradation.
- The existing cache policy worked as intended: accepted incumbent artifacts were sufficient for candidate comparison, avoiding unnecessary incumbent reruns.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as `db2387935aa0937eb8669de20843dc3caaccb115`
- Research state updated: ready proposal removed after acceptance
- Leaderboard updated: yes
- Git status checked: yes

## Next Action

Continue the optimization loop with a fresh Researcher proposal batch using `dino_ri2m_ekman_depth_orolift_lwind` as the new incumbent.

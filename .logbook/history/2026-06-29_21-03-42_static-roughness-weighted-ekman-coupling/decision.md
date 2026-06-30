# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.16500609426017815
- Iteration incumbent primary score: -0.16500618979404214
- Iteration delta: +0.00000009553386398630792
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.16591150807771451
- Validation delta: not applicable

## Rationale

The candidate was numerically stable and guardrail-clean, but it did not clear the fixed iteration promotion threshold. The iteration delta was +0.00000009553386398630792, far below the required +0.002, so validation was skipped according to `roles/PROTOCOL.md`.

Fast and iteration diagnostics were clean: `failed=false` and issue count `0`. Unit tests passed with `283 passed, 2 skipped`. RMSE guardrails were also clean: the largest early-lead mean regression was `10m_u_component_of_wind` at +0.000019102354370693865%, below the 2% threshold, and the largest single-lead regression was `geopotential_500` at 24h with +0.0001657404768912333%, below the 10% threshold.

The incumbent was not rerun. The Scorer reused the valid cached iteration artifact for `dino_ri2m_ekman_coupled` from `outputs/eval/iteration_dino_ri2m_ekman_coupled.json`; candidate source edits do not invalidate the accepted incumbent cache under the current protocol.

## Lessons Learned

- A bounded, area-normalized land/sea/coast roughness redistribution of the accepted Ekman stress-pumping closure is stable but effectively neutral.
- The accepted uniform coupled Ekman coefficient appears to capture nearly all useful signal available from this coarse static land-sea roughness proxy.
- Future roughness proposals should stay staged unless they bring a stronger static proxy, such as validated roughness length or terrain class fields, without weakening the accepted Ekman balance.

## Cleanup Completed

- Candidate code retained or reverted: reverted with `.logbook/history/2026-06-29_21-03-42_static-roughness-weighted-ekman-coupling/candidate.diff` applied in reverse.
- Research state updated: selected proposal moved to this immutable history directory before implementation; no selected proposal remains in `ready`.
- Leaderboard updated: no; rejected candidates do not update `.logbook/leaderboard.json`.
- Git status checked: tracked source/test changes are clean after rollback; the only remaining untracked path is the pre-existing `gifs/` directory.

## Next Action

Continue the optimization loop with a new Researcher proposal cycle. Do not revisit this exact roughness candidate unless a future proposal changes the physical proxy or coupling mechanism, not just constants.

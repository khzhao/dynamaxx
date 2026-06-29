# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.16408904344830819
- Iteration incumbent primary score: -0.16500618979404214
- Iteration delta: +0.000917146345733949
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.16591150807771451
- Validation delta: not applicable

## Rationale

The candidate was stable and guardrail-clean, but it did not clear the fixed iteration promotion threshold. The iteration delta was +0.000917146345733949, below the required +0.002, so validation was skipped according to `roles/PROTOCOL.md`.

Fast and iteration diagnostics were clean: `failed=false` and issue count `0`. Unit tests passed with `280 passed, 2 skipped`. RMSE guardrails were also clean: the largest early-lead mean regression was `geopotential_500` at +0.014313359049992355%, below the 2% threshold, and the largest single-lead regression was `geopotential_500` at 192h with +0.021754943631316342%, below the 10% threshold.

The incumbent was not rerun. The Scorer reused the valid cached iteration artifact for `dino_ri2m_ekman_coupled` from `outputs/eval/iteration_dino_ri2m_ekman_coupled.json`; candidate source edits do not invalidate the accepted incumbent cache under the current protocol.

## Lessons Learned

- Adding a bounded lower-layer pressure-work temperature response to the accepted Ekman pumping closure is numerically stable and slightly improves the iteration primary score, but the improvement is too small to justify validation or replacement of the incumbent.
- The response improved 2 m temperature and 10 m zonal wind RMSE slightly while introducing a very small geopotential_500 regression; future thermal-coupling ideas should focus on preserving mid-tropospheric height skill.
- Cached incumbent artifacts remained valid and avoided unnecessary incumbent recomputation.

## Cleanup Completed

- Candidate code retained or reverted: reverted with `.logbook/history/2026-06-29_13-02-18_ekman-pressure-work-thermal-coupling/candidate.diff` applied in reverse.
- Research state updated: selected proposal moved to this immutable history directory before implementation; no selected proposal remains in `ready`.
- Leaderboard updated: no; rejected candidates do not update `.logbook/leaderboard.json`.
- Git status checked: tracked source/test changes are clean after rollback; the only remaining untracked path is the pre-existing `gifs/` directory.

## Next Action

Continue the optimization loop with a new Researcher proposal cycle. Do not revisit this candidate state unless a future proposal provides a materially different, bounded pressure-work mechanism.

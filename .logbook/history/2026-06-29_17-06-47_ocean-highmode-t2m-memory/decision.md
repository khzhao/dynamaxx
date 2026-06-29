# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -0.16534409792665697
- Iteration incumbent primary score: -0.16500618979404214
- Iteration delta: -0.00033790813261483366
- Validation candidate primary score: not run
- Validation incumbent primary score: -0.16591150807771451
- Validation delta: not applicable

## Rationale

The candidate was numerically stable and guardrail-clean, but it regressed the fixed iteration primary score. The iteration delta was -0.00033790813261483366, below the +0.002 promotion threshold, so validation was skipped according to `roles/PROTOCOL.md`.

Fast and iteration diagnostics were clean: `failed=false` and issue count `0`. Unit tests passed with `281 passed, 2 skipped`. RMSE guardrails were also clean: the largest early-lead mean regression was `2m_temperature` at +0.04663942027907426%, below the 2% threshold, and the largest single-lead regression was `2m_temperature` at 144h with +0.14264303350307025%, below the 10% threshold.

The incumbent was not rerun. The Scorer reused the valid cached iteration artifact for `dino_ri2m_ekman_coupled` from `outputs/eval/iteration_dino_ri2m_ekman_coupled.json`; candidate source edits do not invalidate the accepted incumbent cache under the current protocol.

## Lessons Learned

- Ocean high-mode T2m residual memory is stable, but it worsened the broad fixed iteration score and slightly regressed T2m RMSE.
- The accepted low-mode/RI2m T2m path appears stronger than adding a late high-mode ocean remainder, at least with this bounded single-state mechanism.
- Future T2m proposals should avoid narrow high-mode residual persistence unless they have a clearer mechanism for improving primary score, not only preserving guardrails.

## Cleanup Completed

- Candidate code retained or reverted: reverted with `.logbook/history/2026-06-29_17-06-47_ocean-highmode-t2m-memory/candidate.diff` applied in reverse.
- Research state updated: selected proposal moved to this immutable history directory before implementation; no selected proposal remains in `ready`.
- Leaderboard updated: no; rejected candidates do not update `.logbook/leaderboard.json`.
- Git status checked: tracked source/test changes are clean after rollback; the only remaining untracked path is the pre-existing `gifs/` directory.

## Next Action

Continue the optimization loop with a new Researcher proposal cycle. Do not revisit this candidate state unless a future proposal changes the physical mechanism rather than only the ramp, cap, or decay constants.

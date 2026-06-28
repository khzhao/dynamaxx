# Decision Record

## Decision

`accepted`

## Score Summary

- Fast candidate primary score: -1.2475800298776727
- Fast diagnostics: passed, issue count 0
- Iteration candidate primary score: -1.2854136202685928
- Iteration incumbent primary score: -1.3208025947740873
- Iteration delta: +0.0353889745054945
- Validation candidate primary score: -1.2725740410982802
- Validation incumbent primary score: -1.308334010223954
- Validation delta: +0.03575996912567381

## Rationale

The candidate passed the fast diagnostic gate with no nonfinite or diagnostic issues. It exceeded the iteration promotion threshold by improving primary score by `+0.0353889745054945`, above the required `+0.002`, while preserving clean diagnostics and passing RMSE guardrails. It then exceeded the validation acceptance threshold by improving primary score by `+0.03575996912567381`, above the required `+0.001`, again with clean diagnostics and no early-lead or per-variable/lead RMSE guardrail failure.

Corrected RMSE checks compare only candidate and incumbent model rows, excluding persistence rows. Early lead 1-5 mean RMSE improved by about 10.16% for iteration `2m_temperature` and 1.69% for iteration `10m_u_component_of_wind`, with similar validation improvements. Pressure-level and mean-sea-level-pressure RMSE stayed effectively unchanged, with maximum positive per-variable/lead regressions far below the 10% guardrail.

The mechanism is physically and diagnostically plausible for this adapter because it corrects an output diagnostic mismatch introduced when mapping the analysis into the Dinosaur forecast/output path, without changing the prognostic trajectory or expanded evaluation contract. The candidate is retained as a side-by-side registered model.

## Lessons Learned

- Near-surface diagnostic residual correction can recover a large fixed-protocol score gap without perturbing pressure-level mass fields.
- Correct guardrail scripts must filter explicit model rows when evaluation artifacts also contain persistence references.
- Output-only adapters can be valid model-selection candidates when they preserve deterministic forecast shape, target variables, leads, and metrics.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as `845de671268f42c6b44b0a60c287e043087364a1`.
- Research state updated: removed from `.logbook/research/ready`; immutable copy retained in this history directory.
- Leaderboard updated: yes, incumbent pointer now references `dinosaur_dfi_surface_residual`.
- Git status checked: clean tracked worktree after commit.

## Next Action

Continue the loop by re-inspecting resources and git state, then triage the remaining staged proposal against the accepted `dinosaur_dfi_surface_residual` incumbent. Do not run `golden`.

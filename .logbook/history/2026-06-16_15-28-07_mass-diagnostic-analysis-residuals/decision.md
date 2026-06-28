# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: -1.2470991177529807
- Fast diagnostics: passed, issue count 0
- Iteration candidate primary score: -1.284988567046514
- Iteration incumbent primary score: -1.2854136202685928
- Iteration delta: +0.00042505322207886387
- Validation candidate primary score: not run
- Validation incumbent primary score: -1.2725740410982802
- Validation delta: not run

## Rationale

The candidate passed fast diagnostics and iteration diagnostics with no nonfinite or diagnostic issues. It also passed the fixed RMSE guardrails: no early lead 1-5 mean RMSE regression exceeded 2%, and no variable/lead RMSE regression exceeded 10%.

The iteration primary-score improvement was `+0.00042505322207886387`, below the required `+0.002` promotion threshold. Because the candidate did not promote on iteration, validation was not run. The measured RMSE movement was clean but too small to justify replacing the incumbent.

## Lessons Learned

- Decaying output residuals for mass diagnostics are safe under the fixed guardrails but have low signal after the accepted near-surface residual incumbent.
- The rejected terrain candidate showed mass-field residual changes can be dangerous when coupled to prognostic surface pressure or orography; this output-only version avoided that failure mode but did not produce enough primary-score gain.
- Further residual-style candidates should require stronger evidence of residual magnitude before consuming full iteration resources.

## Cleanup Completed

- Candidate code retained or reverted: reverted after rejection; no source commit made.
- Research state updated: removed from `.logbook/research/ready`; immutable copy retained in this history directory.
- Leaderboard updated: no; incumbent remains `dinosaur_dfi_surface_residual`.
- Git status checked: clean tracked worktree after rollback.

## Next Action

Continue the loop by re-inspecting resources and git state, then run a fresh Researcher/Evaluator pass because no ready proposal remains. Do not run `golden`.

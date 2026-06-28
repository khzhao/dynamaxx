# Decision Record

## Decision

`rejected`

## Score Summary

- Fast candidate primary score: -1.7976931348623157e+308
- Fast candidate diagnostics: failed, `nonfinite_forecast`, value 4713420
- Iteration candidate primary score: not_run
- Iteration incumbent primary score: not_run
- Iteration delta: not_run
- Validation candidate primary score: not_run
- Validation incumbent primary score: not_run
- Validation delta: not_run

## Rationale

The candidate passed unit tests but failed the required fast diagnostic gate. The fixed fast evaluation for `dinosaur_moist` exited with process status 0, but `outputs/eval/fast_dinosaur_moist.json` reported `diagnostics.failed=true` with one error: `nonfinite_forecast`, value 4713420. Under `roles/PROTOCOL.md`, `fast` must complete without forecast or metric diagnostic failure before iteration is run.

Because the fast gate failed, the candidate was not eligible for iteration or validation. No leaderboard update was made.

## Lessons Learned

- Enabling the existing moist dynamics path is not sufficient as a standalone model-selection candidate under the fixed diagnostics.
- Future work on this mechanism should first isolate whether nonfinite lower-pressure-level outputs arise from moist dynamics, pressure interpolation at deep levels, or full-output diagnostics shared with the dry adapter.
- Any repair to evaluation support or diagnostic masking must be proposed and accepted separately before it can affect model-selection scoring.

## Cleanup Completed

- Candidate code retained or reverted: reverted. The `dinosaur_moist` factory, export, registry entry, and tests were removed.
- Research state updated: removed from `.logbook/research/ready`; immutable copy retained in this history directory.
- Leaderboard updated: no.
- Git status checked: clean after rollback.

## Next Action

Continue the loop by generating or re-triaging proposals. The current ready directory is empty; staged ideas remain available for future evaluation.

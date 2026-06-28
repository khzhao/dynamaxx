# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.2252107539770965`
- Iteration incumbent primary score: `-0.2197104515448394`
- Iteration delta: `-0.005500302432257104`
- Validation candidate primary score: not run
- Validation incumbent primary score: not used
- Validation delta: not run

## Rationale

The candidate passed the full unit suite, fast gate, and iteration diagnostics, but failed the fixed iteration promotion gate. The iteration primary score regressed by `-0.005500302432257104` relative to the cached incumbent, while promotion requires at least `+0.002`.

The fixed RMSE guardrails also failed. The largest early day 1-5 mean RMSE regression was `+0.6689371902001219` for `2m_temperature`, above the `+0.02` threshold. The worst variable-lead regression was `+1.1236482423343757` for `2m_temperature` at `288h`, above the `+0.10` threshold. Validation was therefore skipped.

## Lessons Learned

- Sheltering the lower sigma layers of the accepted vertical-DSE increment is too damaging to T2m skill, even though some free-tropospheric and wind RMSEs improve.
- The accepted pressure-ramped vertical-DSE increment appears to require its lower-column contribution for the current fixed-score balance.
- Future Researcher proposals should deprioritize simple damping of the incumbent vertical-DSE increment and instead consider mechanisms that correct T2m without suppressing the accepted column redistribution.

## Cleanup Completed

- Candidate code retained or reverted: reverted after history artifacts were written.
- Research state updated: proposal copied into history and removed from `.logbook/research/ready`.
- Leaderboard updated: no; rejected candidates do not update the leaderboard.
- Git status checked: clean for tracked files; only protected pre-existing `gifs/` remains untracked.

## Next Action

Continue the optimization loop with the next Researcher/Evaluator-selected proposal.

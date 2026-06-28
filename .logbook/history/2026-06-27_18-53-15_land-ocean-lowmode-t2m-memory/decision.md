# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.21638012219181893`
- Iteration incumbent primary score: `-0.2197104515448394`
- Iteration delta: `+0.003330329353020467`
- Validation candidate primary score: `-0.21606470816567627`
- Validation incumbent primary score: `-0.21940899263836755`
- Validation delta: `+0.003344284472691278`

## Rationale

The candidate passed all fixed gates. Unit tests and fast evaluation passed, iteration improved over the cached incumbent by more than the `+0.002` promotion threshold, and validation improved over the cached incumbent by more than the `+0.001` acceptance threshold. Candidate diagnostics were clean for fast, iteration, and validation.

The regression guardrails also passed. On validation, the worst candidate-row variable-lead RMSE regression was `8.760358627402098e-7` for 500 hPa geopotential at 168 hours, far below the `10%` guardrail. Day-1-through-day-5 mean RMSE regressions by target variable were all far below `2%`. No nonfinite output, unstable output, severe oversmoothing, or forecast-contract change was observed.

Incumbent iteration and validation metrics were reused from the leaderboard cache because the incumbent model, data path, target variables, lead range, protocols, and metric artifacts were compatible and readable. No incumbent rerun was performed.

## Lessons Learned

- A late-ramped, capped broad T2m residual memory can recover useful skill without spending early-lead guardrail budget.
- Future scorer comparisons must filter metric records by `model_name` before pairing variable/lead rows because evaluation artifacts include persistence records with duplicate variable/lead keys.
- The next research pass should look for similarly isolated improvements that do not perturb the accepted WTG and vertical-DSE dynamics unless there is a stronger mechanistic reason.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as `d1f132fafcad09bcc92cfeedbe3fc2be1b930770`.
- Research state updated: ready proposal moved to this history directory.
- Leaderboard updated: yes, now points to `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem`.
- Git status checked: yes; tracked worktree clean after commit, with pre-existing untracked `gifs/` preserved.

## Next Action

Start the next continuous optimization iteration from the accepted `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem` incumbent.

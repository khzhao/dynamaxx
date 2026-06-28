# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.21299732605547173`
- Iteration incumbent primary score: `-0.21638012219181893`
- Iteration delta: `+0.0033827961363472048`
- Validation candidate primary score: `-0.21274255459898536`
- Validation incumbent primary score: `-0.21606470816567627`
- Validation delta: `+0.0033221535666909108`

## Rationale

The candidate passed all fixed gates. Full unit tests and fast evaluation passed, iteration improved over the cached incumbent by more than the `+0.002` promotion threshold, and validation improved over the cached incumbent by more than the `+0.001` acceptance threshold. Candidate diagnostics were clean for fast, iteration, and validation.

Regression guardrails also passed. On validation, the worst candidate-row variable-lead RMSE regression was `0.0002992156303169846` for `2m_temperature` at 48 hours, far below the `10%` guardrail. Day-1-through-day-5 mean RMSE regressions by target variable were all far below `2%`. No nonfinite output, unstable output, severe oversmoothing, or forecast-contract change was observed.

Incumbent iteration and validation metrics were reused from the leaderboard cache because the incumbent model, data path, target variables, lead range, protocols, and metric artifacts were compatible and readable. No incumbent rerun was performed.

## Lessons Learned

- T2m still had exploitable error after the accepted broad land/ocean residual memory; a tightly capped raw screen-temperature diagnostic improved both iteration and validation.
- The next research pass should consider low-blast-radius corrections for the remaining negative MSLP channel, with `persistent-mslp-reduction-offset` already ready as the top remaining proposal.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as `3992244f20b2a938fdd96f8904f3749f5505670d`.
- Research state updated: selected ready proposal moved to this history directory.
- Leaderboard updated: yes, now points to `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m`.
- Git status checked: yes; tracked worktree clean after commit, with pre-existing untracked `gifs/` preserved.

## Next Action

Start the next continuous optimization iteration from the accepted `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m` incumbent. The remaining ready proposal is `persistent-mslp-reduction-offset`.

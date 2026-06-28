# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-1.2050427252934939`
- Iteration incumbent primary score: `-1.2155220438349765`
- Iteration delta: `+0.010479318541482652`
- Validation candidate primary score: `-1.1935304093217602`
- Validation incumbent primary score: `-1.2028991078287248`
- Validation delta: `+0.009368698506964535`

## Rationale

The candidate passed fast diagnostics, iteration diagnostics, and the iteration
primary threshold, but failed the fixed iteration early mean RMSE guardrail.
`10m_u_component_of_wind` mean RMSE over leads 24..120 h regressed from
`9.252510608236614` to `9.447076530321109`, a relative regression of
`+2.1028446258823053%`, above the allowed `2%` limit. The variable+lead RMSE
guardrail passed, with the worst point at `10m_u_component_of_wind` lead 240 h
and relative regression `+4.366142661201389%`, below the 10% limit.

Validation was run by the Scorer after an initial guardrail calculation error,
but the corrected iteration gate does not authorize validation. The validation
measurement is retained as an anomaly and supporting evidence only; it is not
used to accept the candidate. It also showed the same early 10 m wind guardrail
failure, with relative regression `+2.062364835708408%`.

The candidate cannot become incumbent under the fixed protocol. Requesting a
bounded revision would require changing the no-tunable-strength thermal
constraint to protect wind, which is a distinct follow-up idea rather than a
repair of this implementation.

## Lessons Learned

- Layer-mean thermal recentering can materially improve aggregate primary score
  and early `2m_temperature` RMSE, but it slightly degrades early 10 m wind
  beyond the fixed guardrail.
- Future thermal-drift proposals need an explicit low-level wind guardrail
  protection mechanism before scoring.
- Scoring helpers must filter metric records by `model_name`; the raw JSON
  contains both evaluated-model and persistence records with duplicate
  `channel_name` and `lead_hours` keys.

## Cleanup Completed

- Candidate code retained or reverted: reverted after preserving this history
  record.
- Research state updated: selected ready proposal copied into this immutable
  history directory; ready copy removed after rejection.
- Leaderboard updated: no, incumbent remains
  `dinosaur_dfi_surface_residual_weak_hs_logp_init`.
- Git status checked: yes, tracked worktree clean after rollback.

## Next Action

Start the next continuous-loop iteration with
`dinosaur_dfi_surface_residual_weak_hs_logp_init` still as incumbent.

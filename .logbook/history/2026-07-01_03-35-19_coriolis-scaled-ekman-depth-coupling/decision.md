# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.13590520069778708`
- Iteration incumbent primary score: `-0.16500618979404214`
- Iteration delta: `+0.029100989096255053`
- Validation candidate primary score: `-0.13767474868567484`
- Validation incumbent primary score: `-0.16591150807771451`
- Validation delta: `+0.02823675939203968`

## Rationale

The candidate passed all fixed gates. Focused tests, full unit tests, fast evaluation, iteration evaluation, and validation evaluation all completed successfully. Candidate diagnostics were clean for fast, iteration, and validation.

Iteration improved over the cached incumbent by `+0.029100989096255053`, above the `+0.002` promotion threshold. Validation improved over the cached incumbent by `+0.02823675939203968`, above the `+0.001` acceptance threshold.

Regression guardrails passed. On iteration, the worst single variable-lead RMSE regression was `1.1898982135831615%` for `2m_temperature` at 360 hours, below the `10%` limit. On validation, the worst single variable-lead RMSE regression was `0.9255849240232976%` for `2m_temperature` at 288 hours. Day-1-through-day-5 mean RMSE improved for every target variable on both iteration and validation. No forecast-contract change was introduced.

Incumbent iteration and validation metrics were reused from the leaderboard cache because the incumbent artifacts were readable, finite, clean, and compatible with the fixed WeatherBench2 protocols, target variables, lead range, data path, and fixed evaluation code. No incumbent rerun was performed.

## Lessons Learned

- A bounded Coriolis-scaled depth and smooth hypsometric stress projection improved the accepted coupled Ekman closure substantially without changing drag strength, output diagnostics, target variables, splits, lead times, or metrics.
- Early-lead improvements were broad across `10m_u_component_of_wind`, `2m_temperature`, `geopotential_500`, and `mean_sea_level_pressure`, with the largest gains in mean sea level pressure.
- Future Ekman-family proposals should avoid immediate coefficient tuning and instead propose clearly distinct mechanisms, because the current accepted geometry change is already a strong incumbent.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as `b40f5515ec79abeec4f10db4addfd0abbe44da13`.
- Research state updated: selected proposal copied into this history directory; active ready/staging copy removed from the research queue.
- Leaderboard updated: yes, now points to `dino_ri2m_ekman_depth`.
- Git status checked: yes before the accepted metadata commit; remaining untracked `gifs/` is unrelated user/generated material and was preserved.

## Next Action

Start the next continuous optimization iteration from the accepted `dino_ri2m_ekman_depth` incumbent, using cached incumbent metrics from the updated leaderboard when valid.

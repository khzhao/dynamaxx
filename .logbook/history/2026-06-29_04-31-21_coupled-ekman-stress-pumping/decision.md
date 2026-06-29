# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: `-0.16500618979404214`
- Iteration incumbent primary score: `-0.21299732605547173`
- Iteration delta: `+0.04799113626142959`
- Validation candidate primary score: `-0.16591150807771451`
- Validation incumbent primary score: `-0.21274255459898536`
- Validation delta: `+0.04683104652127085`

## Rationale

The candidate passed all fixed gates. Focused tests, full unit tests, fast evaluation, iteration evaluation, and validation evaluation all completed successfully. Candidate diagnostics were clean for fast, iteration, and validation.

Iteration improved over the cached incumbent by `+0.04799113626142959`, above the `+0.002` promotion threshold. Validation improved over the cached incumbent by `+0.04683104652127085`, above the `+0.001` acceptance threshold.

Regression guardrails passed. On validation, the worst candidate-row variable-lead RMSE regression was `0.007402305337001447` for `2m_temperature` at 264 hours, below the `10%` guardrail. Day-1-through-day-5 mean RMSE improved for every target variable on both iteration and validation. No forecast-contract change was introduced.

Incumbent iteration and validation metrics were reused from the leaderboard cache because the incumbent artifacts were readable, finite, clean, and compatible with the fixed WeatherBench2 protocols, target variables, lead range, and data path. No incumbent rerun was performed.

## Lessons Learned

- A tightly bounded lower-layer stress closure can improve the fixed score materially when coupled to a mass-neutral log-pressure proxy and protected by no-op and finite-value guards.
- The next research pass should avoid duplicating this accepted surface-stress class unless it proposes a clearly distinct mechanism or bounded revision.

## Cleanup Completed

- Candidate code retained or reverted: retained and committed as `d187308d30a242bf38aabe5b7eb530fca522a68f`.
- Research state updated: selected ready proposal moved to this history directory; rejected peer proposal remained in scrap.
- Leaderboard updated: yes, now points to `dino_ri2m_ekman_coupled`.
- Git status checked: yes; tracked source/test changes were committed, and only ignored `gifs/`, `outputs/`, and `.logbook` artifacts remained before the metadata commit.

## Next Action

Start the next continuous optimization iteration from the accepted `dino_ri2m_ekman_coupled` incumbent, using cached incumbent metrics from the updated leaderboard when valid.

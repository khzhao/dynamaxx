# Decision Record

## Decision

`accepted`

## Score Summary

- Iteration candidate primary score: -0.13156559713631472
- Iteration incumbent primary score: -0.13590520069778708
- Iteration delta: +0.004339603561472366
- Validation candidate primary score: -0.13341144990707632
- Validation incumbent primary score: -0.13767474868567484
- Validation delta: +0.004263298778598518

## Rationale

The candidate passed all fixed evaluation gates with the configured local WeatherBench2 path. The incumbent iteration and validation metrics were reused from the valid leaderboard cache, so no incumbent rerun was performed.

Fast, iteration, and validation candidate evaluations completed with clean diagnostics and zero reported issues. The iteration primary-score delta exceeded the +0.002 promotion threshold, and the validation primary-score delta exceeded the +0.001 acceptance threshold.

Guardrails passed. The worst iteration early mean RMSE regression was geopotential_500 at +0.7788865200605566%, below the 2% threshold, and the worst iteration single variable/lead RMSE regression was geopotential_500 at 48 h with +1.0575566129183667%, below the 10% threshold. The worst validation early mean RMSE regression was geopotential_500 at +0.7110242616785794%, below the 2% threshold, and the worst validation single variable/lead RMSE regression was geopotential_500 at 48 h with +0.9455183193520166%, below the 10% threshold.

The mechanism is physically bounded: it uses terrain-gradient upslope/downslope adiabatic thermal increments, suppresses unsupported high-frequency terrain forcing, preserves horizontal mean thermal neutrality, caps each step's projected temperature increment, and leaves the forecast output contract unchanged.

## Lessons Learned

- Cached incumbent metrics are sufficient for comparison when the leaderboard fingerprint still matches the data path, protocol, target variables, lead range, and fixed evaluation code.
- Low-mode orographic thermal tendencies can improve the fixed aggregate score while staying within early-lead and per-variable guardrails.
- Rejected candidate history should stay local/ignored under the clarified accepted-only commit policy; only accepted candidate source, tests, leaderboard, and acceptance artifacts should be committed.

## Cleanup Completed

- Candidate code retained or reverted: retained
- Research state updated: ready proposal removed after acceptance
- Leaderboard updated: yes
- Git status checked: yes, after source commit the only visible untracked path was the pre-existing `gifs/` directory

## Next Action

Continue the optimization loop with a new Researcher/Evaluator pass using `dino_ri2m_ekman_depth_orolift_theta` as the incumbent and cached incumbent metrics from the updated leaderboard.

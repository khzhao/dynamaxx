# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: -1.376430535805006
- Iteration incumbent primary score: -1.3251884351511753
- Iteration delta: -0.05124210065383061
- Validation candidate primary score: not_run
- Validation incumbent primary score: -1.3128324262513928
- Validation delta: not_run

## Rationale

The candidate passed unit tests and the fixed fast gate, but failed the iteration promotion gate. The required primary-score delta was at least `+0.002`; the observed delta was `-0.05124210065383061`. The candidate also failed the early-lead mean RMSE gate for `10m_u_component_of_wind`, regressing by `+3.64645557771629%` over lead days 1-5, above the 2% limit.

No target variable and lead exceeded the 10% RMSE regression gate, and diagnostics were clean. Validation was not run because iteration did not promote.

## Lessons Learned

- The fourth-order diffusion shape was too weak or poorly balanced for low-level wind evolution in this adapter, despite keeping the same top-wavenumber damping timescale.
- Future diffusion proposals should be more cautious about early 10m wind degradation and should not assume scale selectivity improves broad WeatherBench2 skill.
- The accepted finite-output infrastructure baseline allowed this candidate to fail for scientific performance rather than diagnostic ambiguity.

## Cleanup Completed

- Candidate code retained or reverted: reverted. The `dinosaur_hyperdiffusion` factory, export, registry entry, and tests were removed.
- Research state updated: removed from `.logbook/research/ready`; immutable copy retained in this history directory.
- Leaderboard updated: no.
- Git status checked: clean after rollback.

## Next Action

Continue the loop by selecting another staged idea or asking Researcher for a new proposal. Do not run `golden`.

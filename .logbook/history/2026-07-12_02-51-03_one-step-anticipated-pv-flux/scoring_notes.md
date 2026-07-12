# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_rskin_apv`
  exited 0 after 431 seconds with 0 issues, 120 records, and primary score
  `-0.07487637059903021`.
- Iteration promotion gate: passed. The candidate iteration score was
  `-0.07495718284454471`; the cached incumbent score was
  `-0.07908852007250675`; delta was `+0.004131337227962037`, which is
  `+0.002131337227962037` above the required `+0.002`. Diagnostics were
  clean, all four days-1-5 mean RMSE guardrails passed, and all 60 exact
  target/lead comparisons passed the 10% limit.
- Validation acceptance gate: passed as a measurement. The candidate
  validation score was `-0.07524184185018803`; the cached incumbent score was
  `-0.07929026517101266`; delta was `+0.004048423320824626`, which is
  `+0.003048423320824626` above the required `+0.001`. Diagnostics were
  clean, all four days-1-5 mean RMSE guardrails passed, and all 60 exact
  target/lead comparisons passed the 10% limit.
- Physical plausibility: passed within the fixed scored evidence. Every metric
  was finite, all fixed diagnostics were clean, the worst single RMSE
  regression was 2.284144% at validation MSLP 48h, and days-6-15 mean RMSE
  improved for every target on both iteration and validation. No additional
  qualitative protocol was authorized.

## RMSE Guardrails

The per-target maxima below are maxima over all 15 fixed lead times, so they
cover all 60 target/lead comparisons for each real-data protocol.

| Protocol | Target | Days 1-5 mean regression | Worst lead regression | Gate |
| --- | --- | ---: | ---: | --- |
| iteration | 2m_temperature | -0.617962% | -0.343775% at 24h | pass |
| iteration | mean_sea_level_pressure | +1.358048% | +2.172795% at 48h | pass |
| iteration | geopotential_500 | +0.367093% | +1.603044% at 24h | pass |
| iteration | 10m_u_component_of_wind | +0.370490% | +0.852276% at 24h | pass |
| validation | 2m_temperature | -0.592807% | -0.341529% at 24h | pass |
| validation | mean_sea_level_pressure | +1.457274% | +2.284144% at 48h | pass |
| validation | geopotential_500 | +0.261137% | +1.522243% at 24h | pass |
| validation | 10m_u_component_of_wind | +0.408936% | +0.897362% at 24h | pass |

- Iteration early-mean violations: 0 of 4.
- Iteration per-lead violations: 0 of 60.
- Validation early-mean violations: 0 of 4.
- Validation per-lead violations: 0 of 60.

## Commands And Artifacts

| Command | Exit | Elapsed | Result artifacts |
| --- | ---: | ---: | --- |
| `uv run dynamaxx-eval fast --model dino_rskin_apv` | 0 | 431s | `outputs/eval/fast_dino_rskin_apv.{json,csv}` |
| `uv run dynamaxx-eval iteration --model dino_rskin_apv --workers 4` | 0 | 13837s | `outputs/eval/iteration_dino_rskin_apv.{json,csv}` |
| `uv run dynamaxx-eval validation --model dino_rskin_apv --workers 4` | 0 | 3012s | `outputs/eval/validation_dino_rskin_apv.{json,csv}` |

- Fast SHA-256: JSON
  `4f58f5f9a46bf19222e26ae7630b86cbe6d4aafff600088420b129cbbaca9834`,
  CSV `757ae67eee8f207449deae387e925a422851c885ee4959f5cb906c557e4a1cfb`.
- Iteration SHA-256: JSON
  `590d093b99e0180c46e1e6cb8c4f84d0f36f587daf07cfb60b1dcad00d987214`,
  CSV `254d2166b510a3e9a36314e6ed5a2f53a0afcc557e80703fbce5a30e79f4b826`.
- Validation SHA-256: JSON
  `44ba131f6bab58198393c15166f9ba0233dc4131367168e7624b3d6ffc60d07b`,
  CSV `bdb5ca6eaea982220faa6cc4f7d948d8ffe352395440470196a5a8d70d322e67`.

## Measurement Lessons

- The candidate improves aggregate skill primarily through 2 m temperature
  and geopotential. Mean skill decreases slightly for MSLP and 10 m zonal wind
  on both iteration and validation, but every fixed guardrail remains within
  its limit.
- The APVM tendency has a consistent lead-time signature: small early MSLP,
  geopotential, and wind RMSE costs are followed by days-6-15 improvements in
  every target. Validation reproduces the iteration pattern.
- MSLP is the tightest future constraint. Its validation days-1-5 mean
  regression is 1.457274% against the 2% limit, while its worst individual
  lead regression is 2.284144% against the 10% limit.
- Candidate evaluation cost was 431 seconds for fast, 13,837 seconds for
  iteration, and 3,012 seconds for validation. No same-run incumbent timing was
  measured because incumbent execution was prohibited and unnecessary.

## Anomalies

- Cache reuse: the authoritative incumbent iteration and validation artifacts
  were reused. Requested model, data path, protocol, targets, lead range,
  evaluation code, finite primary scores, diagnostic state, 60 guardrail keys,
  and all four accepted hashes were validated before scoring and audited again
  afterward. Candidate source and registry edits did not invalidate the cache.
- Resource limits: none reached. Four requested workers mapped one-to-one to
  four NVIDIA L4 GPUs for iteration and validation.
- Failed or restarted commands: none. Fast used 1 fresh chunk, iteration used
  229 fresh chunks, and validation used 46 fresh chunks.
- Nonfinite or unstable outputs: none; all three candidate protocols reported
  0 diagnostic issues and finite metric records.
- Command counts: candidate fast 1, candidate iteration 1, candidate validation
  1, incumbent 0, golden 0, pytest by Scorer 0, restarts 0.
- Tests: the Scorer relied on the supplied authoritative record of 324 related
  tests passed, 390 full-suite tests passed with 2 skipped, 10 dedicated APVM
  tests passed after lint-only cleanup, Ruff passed, and `git diff --check`
  passed.
- Frozen implementation: the stored candidate patch retained SHA-256
  `c05bf8f247f386bd3148eec6ce33ee2ecc5f403d8073baab7ba0dce01ee30f94`.
  The Scorer did not edit or revert candidate source/tests or protected
  `gifs/`.

## Recommendation To Orchestrator

The candidate passes every measured fast, iteration-promotion,
validation-acceptance, RMSE guardrail, diagnostic, and physical-plausibility
gate. This is a gate recommendation only; the Orchestrator retains decision
authority.

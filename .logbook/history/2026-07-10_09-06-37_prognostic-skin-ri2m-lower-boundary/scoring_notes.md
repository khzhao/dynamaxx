# Scoring Notes

## Gate Status

- Tests: passed. The Orchestrator supplied the completed `uv run pytest`
  result: `325 passed, 2 skipped` in `313.77 s`. The Scorer verified that
  record and did not rerun the suite.
- Fast gate: passed. The candidate score was
  `-0.10523341113437608`; diagnostics reported `failed=false`, zero issues,
  and 120 total records containing 60 exact candidate records and 60
  persistence records.
- Iteration promotion gate: passed. The candidate score was
  `-0.10655439732760863` against cached incumbent
  `-0.1102658536572533`, a delta of `+0.0037114563296446745` against the
  required `+0.002`. Diagnostics were clean, every days 1-5 variable mean
  RMSE regression was below `2%`, and the maximum variable/lead regression
  was below `10%`.
- Validation acceptance gate: passed as a measurement. The candidate score
  was `-0.10736873851248371` against cached incumbent
  `-0.11137528326510353`, a delta of `+0.0040065447526198145` against the
  required `+0.001`. Diagnostics were clean and every days 1-5 variable mean
  RMSE regression was below `2%`.
- Golden: not run.

### Early Mean RMSE Guardrail

| Protocol | Variable | Candidate | Incumbent | Regression | Gate |
| --- | --- | ---: | ---: | ---: | --- |
| iteration | 2m_temperature | 4.4621043137314516 | 4.4621042907496085 | +0.0000005150449622348674% | pass |
| iteration | mean_sea_level_pressure | 651.8563674102227 | 651.8563395366289 | +0.000004276033238603816% | pass |
| iteration | geopotential_500 | 560.628379572417 | 560.6283502011624 | +0.000005238988443068138% | pass |
| iteration | 10m_u_component_of_wind | 3.8618499043591386 | 3.861850497038673 | -0.000015347034665325054% | pass |
| validation | 2m_temperature | 4.45878269308482 | 4.458784505836845 | -0.000040655744237838576% | pass |
| validation | mean_sea_level_pressure | 639.7770656996028 | 639.7770384360099 | +0.00000426142097165183% | pass |
| validation | geopotential_500 | 553.3175356603272 | 553.3175897422246 | -0.000009774114984040239% | pass |
| validation | 10m_u_component_of_wind | 3.826420627329381 | 3.826419692168264 | +0.00002443958562192705% | pass |

### Maximum Variable/Lead Regression

- Iteration: Z500 at `264 h`, candidate RMSE
  `1051.4052481111887` versus incumbent `1051.4048811584278`, absolute
  change `+0.00036695276094178553`, relative regression
  `+0.000034901184831070964%`; the `10%` guardrail passed.
- Validation: Z500 at `24 h`, candidate RMSE `234.86707859162462` versus
  incumbent `234.86622431060155`, absolute change
  `+0.0008542810230665054`, relative regression
  `+0.0003637308964243857%`. This is reported for completeness; validation's
  fixed gate uses the days 1-5 variable means rather than the iteration-only
  `10%` variable/lead guardrail.

## Measurement Lessons

- The score movement reproduced on both independent promotion splits. The
  candidate improved primary score by `+0.0037114563296446745` on iteration
  and `+0.0040065447526198145` on validation.
- Mean T2m RMSE over leads 6-15 improved by `0.07982718618523776 K`
  (`1.1197409863035523%`) on iteration and `0.08479064331858588 K`
  (`1.1934339610404021%`) on validation. This is consistent with the
  late-ramped skin observer hypothesis.
- Non-T2m differences were numerical-scale. Across validation leads 6-15,
  absolute mean RMSE changes were below `0.0011` in each non-T2m metric. The
  largest reported regression was also far below every fixed guardrail.
- Exact-model filtering selected 60 candidate or incumbent rows per protocol;
  all persistence rows were excluded from candidate/incumbent regression
  calculations.

## Anomalies

- Cache reuse: incumbent iteration and validation metrics were reused from
  `.logbook/leaderboard.json`; the incumbent was not rerun. The requested
  incumbent exactly matched the leaderboard, the data path, protocols,
  targets, and lead range matched, and evaluation code was compatible with
  `b92c07d2f054bd34cb90d36592501c5ff74c5991`. Changes after that source
  commit are accepted logbook metadata plus the frozen candidate source/test
  patch, which does not invalidate the cache under the protocol.
- Cache artifacts: iteration JSON SHA-256
  `8791fe8e832bb19cc7504436065f0cc3fcb0f5e042f73a41e2b1f3bc26bc27f3`;
  validation JSON SHA-256
  `13ea8886ee66f7967e198d87059f85bfef2913bf2ad113ebfb2d8d582e5d99c3`.
  Each artifact was readable, finite, clean, and contained 60 exact incumbent
  plus 60 persistence records and all required guardrail keys.
- Resource limits: no limit was reached. Fast, iteration, and validation used
  four effective workers dispatched one per available NVIDIA L4 GPU.
- Failed or restarted commands: none. Fast completed 1/1 chunk, iteration
  229/229 chunks, and validation 46/46 chunks without retry.
- Nonfinite or unstable outputs: none reported by forecast or metric
  diagnostics.
- Frozen patch: the live six-file diff and saved `candidate.diff` both have
  SHA-256 `fc98be9af6ddbda66636fb89717b7339d29f7fa23f4adfe8ba139178af233758`.
  The Scorer did not modify source, tests, roles, evaluation code, leaderboard,
  or `gifs/`.

## Recommendation To Orchestrator

Fast, iteration, and validation passed every measured fixed gate. Recommend
that the Orchestrator proceed to its acceptance review. This report is a
Scorer recommendation only and does not accept or reject the candidate.

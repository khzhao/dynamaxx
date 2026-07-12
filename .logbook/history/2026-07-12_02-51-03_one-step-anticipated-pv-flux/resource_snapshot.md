# Resource Snapshot

- Recorded at: `2026-07-12T02:51:03Z`
- Baseline HEAD: `d48e1df095fbbfe6ccd2c64688c60b24e22a4d01`
- Accepted incumbent source commit: `8d8b2cba4399bf9f35689c4e55855e2436d367a6`
- Baseline git status: only protected pre-existing `?? gifs/`
- CPU cores: 48
- Available RAM: 185,009,528,832 bytes
- GPUs: four NVIDIA L4 devices, each with 22,566 MiB free of 23,034 MiB and 0% utilization
- Free disk for repository and evaluation outputs: 4,439,763,410,944 bytes
- Evaluation workers: 4
- Worker rationale: four idle GPUs are available; RAM exceeds 128 GiB; four workers are below half the CPU count and preserve substantial memory and disk headroom.
- WeatherBench2 path: `/home/ubuntu/data/weathermaxx-data/weatherbench2/datasets/v1/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative`

## Incumbent Cache

The leaderboard names `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori_rskin` as the accepted incumbent. Its evaluation fingerprint matches the fixed data path, protocols, target variables, lead range, and accepted evaluation-code commit. All artifacts are present, readable, finite, and retain their accepted hashes, so no incumbent evaluation is authorized for this iteration.

- Iteration score: `-0.07908852007250675`
- Validation score: `-0.07929026517101266`
- Iteration JSON SHA-256: `4097de3f1dfc95a978e85c45a9e77d4a15a46f7feead6260c945617c3e888471`
- Iteration CSV SHA-256: `62cce8abb724e50a6ff2f75857aa51fb9eb1c5dd622bab5ff3e7c836b9dc943c`
- Validation JSON SHA-256: `663ec458c764e4d169842f71d129da349fab52dc2dc735b3279c1e30e52cbecf`
- Validation CSV SHA-256: `3d1cda55f61c2bec08f8ccb0900a4352b6385e8e2d83d73a72e53177d9d4cd08`

## Selection

- Selected proposal: `one-step-anticipated-pv-flux`
- Frozen proposal SHA-256: `b7dc7f90568b8e7699990ac65ebbccd3de7fb9d82ec886e59f896f2134a5f35e`
- Candidate model key: `dino_rskin_apv`
- Implementation mode: one side-by-side incumbent-derived registered model
- Fixed gates: full unit tests, candidate fast, candidate iteration, and candidate validation only after iteration promotion
- Golden evaluations: prohibited
- Incumbent evaluations: prohibited unless a concrete cache-invalidating condition is discovered and recorded

## Pre-Scoring Refresh

- Available RAM: 184,855,207,936 bytes
- GPUs: four NVIDIA L4 devices, each with 22,566 MiB free and 0% utilization
- Free disk: 4,439,730,724,864 bytes
- Git state: only the frozen seven-file candidate diff plus protected `?? gifs/`
- Worker allocation remains 4.

## Accepted Source Identity

- Candidate source commit: `7174848c3641a43299fc5c2682bef2fc75f2ff89`
- The source commit contains exactly the seven files captured by `candidate.diff` and includes the full positive-commit protocol body.

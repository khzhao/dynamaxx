# Resource Snapshot

## Identity

- Proposal slug: analysis-2m-initialized-land-skin-memory
- Candidate model name: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si
- Incumbent model name: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri
- Snapshot time: 2026-07-10T23:59:52Z

## Git State

- HEAD: 07cf68b922784894415df64e36368a60f2df5080
- Incumbent source commit: 3fb32ff048b00b779d7e16a2c72e728866a4f4ba
- Worktree before implementation: no tracked changes; pre-existing untracked
  `gifs/` is user-owned and must not be touched
- Selected ready proposal:
  `.logbook/research/ready/analysis-2m-initialized-land-skin-memory.md`

## Incumbent Cache

- Iteration primary: `-0.10655439732760863`
- Validation primary: `-0.10736873851248371`
- Iteration metrics:
  `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri.json`
- Validation metrics:
  `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri.json`
- Cache validity: valid for incumbent identity/source commit, fixed data path,
  protocols, targets, lead days, clean diagnostics, finite scores, and complete
  60-model plus 60-persistence records.

## Evaluation Fingerprint

- Data path:
  `/home/ubuntu/data/weathermaxx-data/weatherbench2/datasets/v1/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative`
- Protocols: fast, iteration, validation
- Target variables: 2m_temperature, mean_sea_level_pressure,
  geopotential_500, 10m_u_component_of_wind
- Lead days: 1..15
- Golden: prohibited for iterative selection

## Machine Resources

- Memory available: about 173 GiB
- GPUs: 4 idle NVIDIA L4 devices after prior scoring cleanup
- Disk available: about 4135 GiB
- Selected evaluation workers: 4

## Fixed Implementation Scope

- Implement one side-by-side candidate initialized from lead-zero analyzed T2m
  only at finite, positive, active-land cells after unit and latitude conversion.
- Initialize both skin and deep to the same analysis value; no blend, smoothing,
  bias correction, land class, second memory, or alternate endpoint.
- Ocean, below-threshold land, missing channel, incompatible shape, invalid
  mask, and each invalid T2m cell use the exact incumbent post-DFI lowest-layer
  initialization without contaminating valid cells.
- Preserve exact atmospheric and emitted-output parity through 120 h. Keep DFI,
  residual memory, dynamics, exchange, skin evolution, caps, mask threshold,
  ramp, RI2m observer, and all accepted constants unchanged.
- Keep the deterministic forecast contract and trajectory count unchanged.
- One implementation only; do not combine with pressure-thickness initialization
  or any staged idea.
- If iteration delta is below `+0.002`, scrap without tuning or revision.
- Reuse cached incumbent artifacts. Do not rerun incumbent and do not run
  golden.
- Commit only if accepted. Rejected source/history changes remain uncommitted,
  and the exact source/test patch must be reversed.

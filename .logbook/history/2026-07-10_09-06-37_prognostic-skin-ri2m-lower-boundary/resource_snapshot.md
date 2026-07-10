# Resource Snapshot

## Identity

- Proposal slug: prognostic-skin-ri2m-lower-boundary
- Candidate model name: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri
- Incumbent model name: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin
- Snapshot time: 2026-07-10T09:06:37Z

## Git State

- HEAD: 3621797069bc8cd4d7845586b0b6659c045676c9
- Incumbent source commit: b92c07d2f054bd34cb90d36592501c5ff74c5991
- Worktree before implementation: no tracked changes; pre-existing untracked
  `gifs/` is user-owned and must not be touched
- Selected ready proposal:
  `.logbook/research/ready/prognostic-skin-ri2m-lower-boundary.md`

## Incumbent Cache

- Cache source: `.logbook/leaderboard.json`
- Iteration primary: `-0.1102658536572533`
- Validation primary: `-0.11137528326510353`
- Iteration metrics:
  `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin.json`
- Validation metrics:
  `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin.json`
- Cache validity: valid. Model identity, source commit, data path, fixed
  protocols, target variables, lead days 1-15, readable finite artifacts,
  diagnostics, and 60 model plus 60 persistence records match. The artifact
  commit after the source commit changes only accepted `.logbook` files and
  does not invalidate evaluation compatibility.

## Evaluation Fingerprint

- Data path:
  `/home/ubuntu/data/weathermaxx-data/weatherbench2/datasets/v1/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative`
- Protocols: fast, iteration, validation
- Target variables: 2m_temperature, mean_sea_level_pressure,
  geopotential_500, 10m_u_component_of_wind
- Lead days: 1..15
- Golden: prohibited for iterative selection

## Machine Resources

- CPU count: 48
- Memory available: 187693436928 bytes (about 175 GiB)
- GPUs: 4 idle NVIDIA L4 devices, each with 22566 MiB free
- Disk available: 4440074252288 bytes (about 4.0 TiB)
- Selected workers: 4, matching the established scoring configuration and
  remaining within CPU, RAM, and GPU limits.

## Protocol Notes

- Implement exactly one idea: retain the accepted prognostic skin trajectory
  for a bounded land-only RI2m output observer.
- Preserve atmospheric and skin trajectory evolution exactly; only T2m output
  packing may change.
- Reuse the accepted zero-through-120-hour, full-at-240-hour ramp and existing
  RI2m caps/guards without tuning.
- Preserve deterministic one-trajectory forecast inputs and outputs; skin must
  remain outside DFI, primitive state, tracers, and emitted variables.
- Require exact early T2m, ocean/invalid T2m, and all-lead non-T2m parity in
  focused tests.
- Do not rerun the incumbent while its cache remains valid. Do not run golden.
- Revert every candidate source/test change and do not commit history if
  rejected. Commit source/tests first with the positive protocol body only if
  accepted, then commit accepted history and leaderboard separately.

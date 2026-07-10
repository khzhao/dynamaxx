# Resource Snapshot

## Identity

- Proposal slug: late-ramped-skin-reservoir-coupling
- Candidate model name: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin
- Incumbent model name: dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m
- Snapshot time: 2026-07-10T04:01:39Z

## Git State

- HEAD: ac8438a42bec2e0c99300b2ccd13d19e22e3c993
- Incumbent source commit: d0c364cf1973e5f926c7795d266afc6789638fc7
- Worktree before implementation: no tracked changes; pre-existing untracked
  `gifs/` is user-owned and must not be touched
- Selected ready proposal:
  `.logbook/research/ready/late-ramped-skin-reservoir-coupling.md`

## Incumbent Cache

- Cache source: `.logbook/leaderboard.json`
- Iteration primary: `-0.1177416449326221`
- Validation primary: `-0.11891349527750807`
- Iteration metrics:
  `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m.json`
- Validation metrics:
  `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m.json`
- Cache validity: valid for the fixed data path, protocols, target variables,
  lead days 1-15, metrics, and accepted evaluation code. Candidate source edits
  do not invalidate it.

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
- Memory available: 187932413952 bytes (about 175 GiB)
- GPUs: 4 idle NVIDIA L4 devices, each with 22566 MiB free
- Disk available: 4439318745088 bytes (about 4.0 TiB)
- Selected workers: 4. This is within the protocol CPU/RAM/GPU limits and
  matches the established successful scoring configuration.

## Protocol Notes

- Implement exactly one idea: a fixed late-ramped force-restore land skin
  reservoir derived from the current incumbent.
- Reuse the rejected reservoir's physical coefficients; do not tune them.
- Keep coupling exactly zero through 120 hours and use one fixed smooth ramp to
  full strength at 240 hours.
- Preserve the deterministic forecast contract and fixed evaluation protocol.
- Do not rerun the incumbent while its cache remains valid.
- Revert all implementation source/test changes and remove the ready marker if
  rejected. Commit only if accepted.

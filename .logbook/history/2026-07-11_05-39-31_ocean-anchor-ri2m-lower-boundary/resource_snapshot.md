# Resource Snapshot

## Identity

- Proposal slug: ocean-anchor-ri2m-lower-boundary
- Candidate model name:
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori`
- Incumbent model name:
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si`
- Snapshot time: 2026-07-11T05:39:31Z

## Git State

- HEAD: `6f4a63731b2dd7598ef9a6c3c085365ceed7aea9`
- Incumbent source commit: `603f44a9b052557bd3bf3a16a9dcd9c05f343449`
- Worktree before implementation: no tracked changes; pre-existing untracked
  `gifs/` is user-owned and must not be touched.
- Selected ready proposal:
  `.logbook/research/ready/ocean-anchor-ri2m-lower-boundary.md`

## Incumbent Cache

- Iteration primary: `-0.08966691030501653`
- Validation primary: `-0.09015390068642175`
- Iteration metrics:
  `outputs/eval/iteration_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si.json`
- Validation metrics:
  `outputs/eval/validation_dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si.json`
- Cache validity: valid for incumbent identity/source commit, fixed data path,
  protocols, targets, lead days, clean diagnostics, finite scores, and complete
  60-model plus 60-persistence records. Candidate source, registry, and test
  edits do not invalidate it.

## Evaluation Fingerprint

- Data path:
  `/home/ubuntu/data/weathermaxx-data/weatherbench2/datasets/v1/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative`
- Protocols: fast, iteration, validation
- Target variables: 2m_temperature, mean_sea_level_pressure,
  geopotential_500, 10m_u_component_of_wind
- Lead days: 1..15
- Golden: prohibited for iterative selection

## Machine Resources

- CPUs: 48
- Memory available: about 174 GiB
- GPUs: 4 idle NVIDIA L4 devices with about 22 GiB free each
- Disk available: about 4134 GiB
- Selected evaluation workers: 4

## Fixed Implementation Scope

- Implement exactly one side-by-side `_ori` descendant of the accepted
  incumbent. Do not combine it with any staged idea.
- Reuse the existing per-initial-condition ocean thermal anchor without
  changing extraction, validation, or prognostic ocean heat-flux use.
- Add only a complementary ocean output observer. Reuse the accepted
  pressure-thickness lower reference, skin-aware Richardson algebra, shear
  floor, hydrostatic height, stability limiter, endpoint bounds, `+/-1.5 K`
  departure cap, and zero-through-120/full-at-240-hour ramp.
- Preserve the accepted land prognostic-skin observer exactly. Land and ocean
  coastal weights must be complementary and must not double count.
- Missing, invalid, nonpositive, nonfinite, shape-incompatible, or unsupported
  dependencies must fall back cell by cell to the exact incumbent output.
- Keep the atmospheric trajectory, ocean forcing, land reservoir, residual
  memory, MSLP, Z500, U10, deterministic forecast contract, trajectory count,
  fixed evaluation protocols, and all accepted constants unchanged.
- If iteration delta is below `+0.002`, scrap without tuning the anchor, cap,
  ramp, mask, blend, or Richardson constants.
- Reuse cached incumbent artifacts. Do not rerun the incumbent and do not run
  golden.
- Commit only if accepted. A rejected implementation and ready proposal are
  reverted/moved without any commit; rejected history remains local and ignored.

# Implementation Record

## Identity

- Proposal slug: absolute-vorticity-flux-dealiasing
- Candidate model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_av_flux_dealias
- Incumbent model name: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual
- Baseline commit: ebdd9463f7f6f682a3f6188ae8be58e70cbd1fa6
- Candidate commit: not committed

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Implemented a side-by-side Dinosaur candidate that adds an opt-in absolute-vorticity flux product dealiasing selector. The selector filters only the nodal momentum flux products built from `(zeta + f) k x v` by transforming those products to modal space, applying a smooth near-truncation attenuation mask, and transforming back before vertical and pressure-gradient terms are added. The incumbent path remains default-false, and the candidate factory preserves the accepted scale-separated residual incumbent options except for the new selector and model name.

The helper falls back to the incumbent product values when filtered fields are nonfinite or shape-incompatible. The same selector is threaded into the primitive-equation object used by rollout and DFI, leaving forecast inputs, outputs, target variables, metrics, lead schedule, residual memory, thermodynamics, scalar advection, pressure-gradient products, diffusion, and evaluation protocols unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | 127 passed in 112.52s. |
| `uv run pytest` | 0 | 193 passed, 2 skipped in 119.32s. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_av_flux_dealias` | not_run | Reserved for Scorer fixed gates. |

## Repair Attempts

- Failure observed: Implementer subagent did not return a final report after targeted tests exited.
- Implementer-owned failure: no source failure observed after main-agent takeover.
- NaN/Inf forecast observed: no.
- Fix attempted: main agent reviewed the patch and reran targeted plus full pytest.
- Follow-up command and result: targeted pytest and full pytest both passed.

## Known Limitations

- The product-filter attenuation is intentionally narrow and may be too weak to move WeatherBench2 metrics if absolute-vorticity flux aliasing is not a material remaining error source.

## Rollback Notes

If rejected, revert only the seven changed source/test files listed above and remove the selected proposal from `.logbook/research/ready`; preserve this history directory and raw evaluation outputs.

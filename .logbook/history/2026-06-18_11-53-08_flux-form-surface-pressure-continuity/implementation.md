# Implementation Record

## Identity

- Proposal slug: `flux-form-surface-pressure-continuity`
- Candidate model name: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_flux_form_logp`
- Incumbent model name: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang`
- Baseline commit: `30a496b1f2ed8f894511404341c7774288bdb4c8`
- Candidate commit: not committed at implementation time
- Implemented at: `2026-06-18T12:09:19Z`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py`
- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

The candidate adds a default-off primitive-equation option,
`use_flux_form_log_surface_pressure_continuity`, and enables it only for the new
side-by-side registered model. The Strang incumbent factory and all prior
factories keep their existing options.

When enabled, the sigma-coordinate explicit `log_surface_pressure` tendency is
augmented with a product-rule correction. The incumbent explicit tendency
continues to compute `-sigma_integral(u dot grad(log_surface_pressure))`, while
the unchanged implicit term contributes the vertically integrated divergence.
The correction replaces the sum of those product-form full continuity terms with
a flux-form full tendency,
`-(1 / surface_pressure) * div(int(surface_pressure * wind d_sigma))`.

The implementation preserves the existing implicit inverse, Coriolis splitting,
DFI algorithm, weak Held-Suarez forcing, near-surface residual correction,
vertical advection option, forecast input/output contract, and evaluation
protocols. To avoid introducing a constant-pressure transform residual, the
flux-form divergence is split into a reference surface-pressure part handled by
the already computed vertically integrated divergence plus an anomaly-flux part
computed with the existing spherical-harmonic `div_cos_lat` operator.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | `80 passed in 70.85s`. |
| `uv run pytest` | 0 | `146 passed, 2 skipped in 77.05s`. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_flux_form_logp` | delegated | Scorer gate in progress. |

## Repair Attempts

- Failure observed: initial focused tests exposed an incorrect flux-divergence path and a constant-pressure correction residual.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: replaced the first flux-divergence path with the dycore's `div_cos_lat` operator for `cos_lat_u`, and split surface pressure into global reference pressure plus anomaly so the constant-pressure correction is zero to roundoff.
- Follow-up command and result: focused tests passed with `80 passed`; full test suite then passed with `146 passed, 2 skipped`.

## Known Limitations

- The flux-form correction adds extra transforms and divergence work to every explicit tendency evaluation when the candidate flag is enabled.
- The implementation is a local product-rule correction within the incumbent semi-implicit sigma-coordinate split; it does not replace the mass coordinate, alter the implicit inverse, or add a global pressure constraint.
- Fixed fast, iteration, and validation scores are measured separately by the Scorer.

## Rollback Notes

If rejected, revert the candidate implementation by removing the
`use_flux_form_log_surface_pressure_continuity` flag, the flux-form correction
helper and diagnostic log-pressure carry-through, the candidate factory/export,
the registry entry, and the focused tests listed above. The proposal and
scoring history should remain in `.logbook/history`.

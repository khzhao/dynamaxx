# Implementation Record

## Identity

- Proposal slug: `symmetric-horizontal-diffusion-split`
- Candidate model name: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_symmetric_diffusion`
- Incumbent model name: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang`
- Baseline commit: `30a496b1f2ed8f894511404341c7774288bdb4c8`
- Candidate commit: not committed at implementation time
- Implemented at: `2026-06-18T13:33:17Z`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

The candidate adds a default-off adapter flag,
`apply_symmetric_horizontal_diffusion_split`, and enables it only in the new
side-by-side registered factory. The candidate preserves every accepted Strang
incumbent option except the candidate name and this rollout diffusion-placement
flag.

For positive-time rollout, the candidate no longer applies the incumbent
full-step horizontal diffusion as a post-step filter. Instead, it builds the
same horizontal diffusion operator with `0.5 * step_seconds` and wraps the
non-Coriolis IMEX step with one half filter before dynamics and one half filter
after dynamics. The accepted symmetric Coriolis wrapper is applied outside that
non-Coriolis step, so the second half diffusion still occurs before the final
half Coriolis rotation.

Digital filter initialization remains on the incumbent full-step post-filter
placement. This keeps the experiment isolated to positive-time diffusion
ordering, as requested by the proposal.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | 0 | `80 passed in 64.51s`. |
| `uv run pytest` | 0 | `146 passed, 2 skipped in 71.02s`. |
| `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_symmetric_diffusion` | delegated | Scorer gate pending. |

## Repair Attempts

- Failure observed: initial implementation omitted registry/dependency tests and one wrapper unit expectation incorrectly expected an unchanged fake field to move.
- Implementer-owned failure: yes
- NaN/Inf forecast observed: no
- Fix attempted: added registry and dependency coverage for the candidate and corrected the local wrapper expectation to assert unchanged divergence when the fake dynamics/filter only modify vorticity.
- Follow-up command and result: focused tests passed with `80 passed`; full test suite passed with `146 passed, 2 skipped`.

## Known Limitations

- The candidate replaces one full modal diffusion post-filter with two half modal filters in rollout, so per-step filter work increases slightly.
- The experiment intentionally leaves DFI on the incumbent filter placement; if accepted or informative, a separate proposal would be needed to test symmetric DFI diffusion placement.
- Fast, iteration, and validation WeatherBench2 scores are measured separately by the Scorer.

## Rollback Notes

If rejected, revert the candidate implementation by removing the
`apply_symmetric_horizontal_diffusion_split` flag, `_symmetric_horizontal_diffusion_step`,
the candidate factory/export, the registry entry, and the focused tests listed
above. The proposal and scoring history should remain in `.logbook/history`.

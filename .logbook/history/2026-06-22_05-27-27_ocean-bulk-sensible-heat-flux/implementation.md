# Implementation

## Baseline

- Baseline commit: `681fe7c0d37fadbc1a91159a8d9a7f9f2543f185`
- Candidate commit: `329dd5758204b7e77f1abb258b1dab9ee5d9b2c8`
- Proposal: `.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux/proposal.md`

## Candidate

- Model name: `dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_scale_surface_residual_analysis_hs_eq_landsea_surface_ocean_bulk_shf`
- Implementation summary:
  - Added an opt-in `apply_ocean_bulk_sensible_heat_flux` adapter flag.
  - Reused the existing land-sea mask loader and validator to construct a Dinosaur-order ocean weight.
  - Built the thermal anchor from finite lead-zero `2m_temperature` when present, or from the initialized lowest-layer full temperature when the T2m channel is absent.
  - Composed a weak explicit ocean-only sensible heat flux into rollout dynamics, changing only the lowest model-layer temperature tendency and leaving the DFI equation on the incumbent path.
  - Bounded strong-wind exchange to a 6 day minimum e-folding time and capped one-step temperature increments at 0.05 K.
  - Added finite guards so invalid mask, anchor, wind, or flux diagnostics reduce to the incumbent added tendency.

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`
- `.logbook/history/2026-06-22_05-27-27_ocean-bulk-sensible-heat-flux/implementation.md`

## Tests And Checks

- `python -m py_compile src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py`
  - Pass
- `python -m py_compile src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py`
  - Pass
- `uv run ruff format src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py`
  - Pass; incidental pre-existing formatting changes were manually restored.
- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'ocean_bulk_shf'`
  - Pass: 6 passed, 98 deselected
- `uv run pytest tests/dycore/test_registry.py -k 'ocean_bulk'`
  - Pass: 1 passed, 19 deselected
- `uv run pytest tests/dycore/models/dinosaur/test_dependency.py -k 'ocean_bulk'`
  - Pass: 1 passed, 18 deselected
- `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py`
  - Pass
- `uv run pytest tests/dycore/models/dinosaur tests/dycore/test_registry.py`
  - Pass: 143 passed, 1 skipped
- Orchestrator review repair:
  - Reordered the DFI equation builder branch so the explicit ocean heat-flux
    anchor cannot enter the DFI equation when Coriolis splitting is enabled.
- `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'ocean_bulk_shf'`
  - Pass: 6 passed, 98 deselected
- `uv run pytest tests/dycore/test_registry.py -k 'ocean_bulk'`
  - Pass: 1 passed, 19 deselected
- `uv run pytest tests/dycore/models/dinosaur/test_dependency.py -k 'ocean_bulk'`
  - Pass: 1 passed, 18 deselected
- `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py`
  - Pass
- `uv run pytest`
  - Pass: 209 passed, 2 skipped in 142.65s

## Repair Attempts

- Orchestrator review found a DFI branch-ordering risk before scoring and
  adjusted the DFI equation selection to keep the heat-flux forcing out of DFI.
  Focused tests and the full test suite passed afterward.
- After running `ruff format`, restored formatter-only changes to pre-existing unrelated code in the large adapter and primitive-equation test files to keep the implementation diff scoped.

## Known Limitations

- The implementation uses initial 2 m air temperature as the ocean anchor when present, not true SST or a prognostic ocean skin temperature.
- The flux has no stability dependence, land flux, momentum drag, drag heating, humidity coupling, new output, or metric change by design.
- Local tests cover helper behavior and registry wiring but do not measure WeatherBench2 skill. Fixed `fast`, `iteration`, and `validation` scoring gates were not run by the Implementer.

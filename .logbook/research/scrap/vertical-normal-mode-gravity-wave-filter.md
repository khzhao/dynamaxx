---
schema_version: 1
slug: vertical-normal-mode-gravity-wave-filter
title: Filter External Gravity Modes in Vertical Normal Coordinates
status: scrap
created_at: 2026-06-19T14:51:51Z
author_role: Researcher
target_model: dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter
expected_code_paths:
  - src/dynamaxx/dycore/models/dinosaur/primitive_equations.py
  - src/dynamaxx/dycore/models/dinosaur/adapter.py
  - src/dynamaxx/dycore/models/dinosaur/__init__.py
  - src/dynamaxx/dycore/registry.py
  - tests/dycore/models/dinosaur/
  - tests/dycore/test_registry.py
expected_eval_protocols:
  - fast
  - iteration
  - validation
---

# Filter External Gravity Modes in Vertical Normal Coordinates

## Hypothesis

The accepted off-centered SIL3 incumbent produced a large improvement by
damping fast-mode/mass-field imbalance, especially late MSLP. The current
off-centering is uniform across the semi-implicit gravity-wave operator. A more
selective filter that damps only the fastest external gravity-wave vertical
normal components after each positive-time step may preserve slow Rossby and
baroclinic modes better than broad horizontal diffusion or another global
off-centering strength change.

This is not another DFI routing, theta recentering, or horizontal diffusion
variant. It targets the vertical modal structure of the linearized
divergence-temperature-log-pressure subsystem that the semi-implicit solver
already constructs.

## Mechanism

Register a side-by-side candidate such as
`dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_vmode_filter`.
Preserve all incumbent physical options and fixed evaluation protocols.

Add an optional positive-time step filter:

- build the linear sigma-coordinate fast-mode operator from the same
  divergence, temperature, and log-surface-pressure blocks used by
  `_get_implicit_term_matrix_sigma`;
- for each total horizontal wavenumber, compute a small vertical eigenbasis for
  the coupled `divergence`, `temperature_variation`, and `log_surface_pressure`
  block using NumPy at trajectory construction time;
- identify the external gravity-wave component by the largest fast-mode
  frequency or by a fixed ordering of the energy-scaled eigenpairs, with tests
  that the selected mode is finite and shape-compatible;
- after each positive-time inner step, project only the modal
  `divergence`/`temperature_variation`/`log_surface_pressure` leaves onto this
  vertical basis and apply a weak exponential damping factor to the selected
  fastest mode, for example an e-folding time of 2 to 4 forecast days;
- leave vorticity, tracers, low-frequency vertical modes, accepted horizontal
  diffusion, theta mean recentering, Richardson 10 m wind diagnostics, and
  near-surface residual correction unchanged;
- keep DFI on the incumbent filter set initially, so this proposal tests
  positive-time mode control rather than another DFI initialization variant;
- fall back to the incumbent state if the projection, reconstruction, or damping
  emits nonfinite values.

The filter should be implemented as a side-by-side step filter, not as a change
to the fixed scoring protocol or as a learned correction.

## Implementation Scope

- Expected files:
  - `src/dynamaxx/dycore/models/dinosaur/primitive_equations.py` if helper
    access to the linear block matrix is needed
  - `src/dynamaxx/dycore/models/dinosaur/adapter.py`
  - `src/dynamaxx/dycore/models/dinosaur/__init__.py`
  - `src/dynamaxx/dycore/registry.py`
  - `tests/dycore/models/dinosaur/test_primitive_equations.py`
  - `tests/dycore/models/dinosaur/test_dependency.py`
  - `tests/dycore/test_registry.py`
- Registry changes:
  - Add one side-by-side factory for the candidate model name above.
- API changes:
  - None. `DycoreModel.forecast`, target variables, output shapes, lead times,
    and evaluation protocols remain unchanged.
- Tests to update:
  - Unit-test vertical-mode basis construction for finite eigenvectors,
    invertible projection/reconstruction, and deterministic mode selection.
  - Verify damping leaves vorticity, tracers, and unselected vertical modes
    unchanged on synthetic states.
  - Verify zero damping exactly reproduces the incumbent state.
  - Verify the candidate factory preserves every incumbent flag except the new
    positive-time vertical normal-mode filter option.
  - Add registry coverage and a finite non-JIT smoke forecast.

## Expected Metric Movement

- Expected improvements:
  - `mean_sea_level_pressure` and `geopotential_500` at medium and long leads if
    residual external gravity-wave energy remains after the accepted 0.05
    off-centering.
  - Possibly `2m_temperature` through cleaner lower-column pressure/thickness
    evolution after the accepted residual decays.
- Expected neutral metrics:
  - `10m_u_component_of_wind` should be less exposed than in low-level drag or
    broad diffusion proposals because vorticity and slow balanced modes are not
    directly damped.
- Possible regressions:
  - If the selected vertical component overlaps materially with useful balanced
    baroclinic evolution, MSLP/Z500 phase can degrade.
  - A poorly conditioned eigenbasis can produce small but systematic spectral
    artifacts even when all fields remain finite.

## Risks

- Numerical stability:
  - Moderate. The filter is bounded and post-step, but it touches prognostic
    mass and thermal state every inner step.
- Compute cost:
  - Low to moderate. Basis construction is small dense linear algebra at model
    setup, and per-step projection cost scales with modal state size. It should
    remain practical under the reported 48 CPU, 173 GiB RAM, and `--workers 4`
    constraints.
- Data leakage:
  - None. The basis uses only fixed vertical coordinates, horizontal
    wavenumbers, and physical constants.
- Physical plausibility:
  - Moderate. Normal-mode methods are a standard way to isolate fast gravity
    modes from slower meteorological modes, but this simplified filter is less
    formal than full nonlinear normal-mode initialization.
- Rollback complexity:
  - Low to moderate. Remove one filter helper, one model option, one
    factory/export, one registry entry, and focused tests if rejected.

## Evaluation Plan

- Fast gate:
  - Run `uv run pytest`.
  - Run `uv run dynamaxx-eval fast --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_vmode_filter`.
  - Require finite forecasts and zero diagnostic issues.
- Iteration gate:
  - Run `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_vmode_filter --workers 4`.
  - Support for the hypothesis is primary-score delta at least `+0.002`,
    clean diagnostics, no early day-1-through-day-5 RMSE guardrail failure, and
    no variable-by-lead RMSE guardrail failure.
- Validation gate:
  - Run `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs_logp_init_hydrostatic_layer_init_coriolis_strang_stability_surface_residual_ri_10m_wind_theta_tendency_theta_mean_recenter_si_offcenter_vmode_filter --workers 4`
    only after iteration promotion.
  - Require validation primary delta at least `+0.001` with the same guardrails.
- Outcome that would falsify the hypothesis:
  - A fast nonfinite output, guardrail failure in early MSLP/Z500, or near-zero
    clean iteration delta would show that mode-selective positive-time damping
    is either unsafe or not a remaining high-leverage error source.

## Citations

- Local history:
  `.logbook/history/2026-06-19_06-50-50_offcentered-semi-implicit-gravity-wave/decision.md`
  accepted off-centered SIL3 with iteration delta `+0.25891536186185515` and
  validation delta `+0.2522585257774621`, showing fast-mode/mass-field control
  is high leverage for the current incumbent.
- Local history:
  `.logbook/history/2026-06-16_19-57-46_divergence-selective-gravity-wave-damping/decision.md`
  rejected a simple divergence damping variant near neutral; this proposal is
  not scalar divergence damping but a vertical-normal-mode projection that
  preserves low-frequency components.
- Daley, R. 1978. "Variational non-linear normal mode initialization." Tellus,
  30, 201-218. The abstract describes nonlinear normal-mode initialization as
  removing spurious high-frequency gravity modes from primitive-equation model
  integrations. https://doi.org/10.3402/tellusa.v30i3.10335
- ECMWF review PDF, "A review of the normal mode initialization method", notes
  the role of normal modes in controlling gravity-wave oscillations:
  https://www.ecmwf.int/sites/default/files/elibrary/1980/9149-review-normal-mode-initialization-method.pdf
- Whitaker, J. S. and Kar, S. K. 2013. "Implicit-Explicit Runge-Kutta Methods
  for Fast-Slow Wave Problems." Monthly Weather Review.
  https://doi.org/10.1175/MWR-D-13-00132.1
- Castanheira, J. M. and Marques, C. A. F. 2020. "Three-dimensional normal mode
  functions: open-access tools for their computation." Geoscientific Model
  Development, 13, 2763-2781. https://doi.org/10.5194/gmd-13-2763-2020

## Researcher Notes

This is decorrelated from active staged `planetary-wave-preserving-horizontal-
diffusion`, `pressure-gradient-product-dealiasing`, and `two-thirds-explicit-
tendency-dealiasing`: those are horizontal spectral/tendency controls, while
this proposal projects the vertical fast-mode subsystem of the semi-implicit
operator. It also differs from `offcenter-damping-theta-energy-return`, which
tries to return numerical damping loss as heat; here the damping is explicitly
mode-selective and does not add compensating thermal energy.

The recent `centered-dfi-offcenter-rollout` and `dfi-theta-mean-recenter`
rejections are treated as negative evidence against DFI routing changes. This
proposal therefore keeps DFI on the incumbent path and only tests
positive-time vertical fast-mode filtering.

## Evaluator Notes

### 2026-06-19T14:56:55Z

Decision: move to `scrap`; ranked 3 of 3 fresh proposals.

The scientific motivation is recognizable: normal-mode methods can separate
gravity-wave components from slower balanced motion, and the accepted
off-centered SIL3 result confirms that fast-mode/mass-field control is
important for this incumbent. The proposed implementation, however, is a poor
next model-selection candidate under the current rubric. It would introduce a
per-wavenumber eigenbasis for the coupled divergence, temperature-variation,
and log-surface-pressure block, choose an external mode by heuristic ordering
or frequency, and apply a projection/reconstruction filter after each
positive-time inner step. That is a high-complexity mode decomposition with
weak local testability: unit tests can prove shapes and finite reconstruction,
but not that the selected mode is the meteorologically harmless component on
the nonlinear sigma-grid forecast.

Recent local evidence further lowers priority. Simple divergence-selective
gravity-wave damping was clean but slightly negative, centered-DFI/offcentered
rollout was clean and essentially neutral, and the accepted off-centering
already supplied the large fast-mode damping gain with only modest late T2m
cost. Existing staged alternatives such as pressure-gradient product
dealiasing and offcenter damping energy return test narrower fast-mode
followups with clearer hooks and smaller implementation surfaces. This proposal
is scrapped for cost-risk tradeoff, not because normal-mode analysis is
unphysical. A future revisit should start as an offline diagnostic proposal
that demonstrates a robust modal separation on incumbent trajectories before
adding a step filter to the model-selection queue.

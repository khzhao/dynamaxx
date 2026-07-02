# Implementation Record

## Identity

- Proposal slug: orographic-lift-adiabatic-tendency
- Candidate model name: dino_ri2m_ekman_depth_orolift_theta
- Incumbent model name: dino_ri2m_ekman_depth
- Baseline commit: b40f5515ec79abeec4f10db4addfd0abbe44da13
- Candidate commit: 7af558f97f2d1286203664f9d6bac17bb8cacbc0

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Implemented an opt-in Dinosaur dycore variant that adds a terrain-gradient adiabatic potential-temperature tendency. The tendency loads WeatherBench2 surface geopotential constants, converts them to terrain height, smooths to low spherical-harmonic modes, projects upslope/downslope wind across the terrain gradient, applies vertical sigma and equatorial tapers, ramps in over the first 48 forecast hours, enforces an area-mean-neutral thermal increment, and caps the projected per-step temperature increment at 0.05 K.

The implementation is registered as `dino_ri2m_ekman_depth_orolift_theta`, keeps the incumbent forecast contract unchanged, leaves momentum/pressure/tracers untouched, and falls back to a no-op when terrain constants are absent, non-finite, or shape-incompatible.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run ruff format src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Formatting completed before scoring. |
| `uv run ruff check src/dynamaxx/dycore/models/dinosaur/adapter.py src/dynamaxx/dycore/models/dinosaur/__init__.py src/dynamaxx/dycore/registry.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/test_registry.py` | 0 | Static checks passed before scoring. |
| Focused pytest for new orographic lift tests | 0 | 9 passed. |
| Registry and dependency pytest subset | 0 | 59 passed. |
| Dinosaur primitive-equation pytest file | 0 | 163 passed. |
| `uv run pytest` | 0 | 288 passed, 2 skipped in 296.58s. |
| `uv run dynamaxx-eval fast --model dino_ri2m_ekman_depth_orolift_theta` | 0 | Primary score -0.1329952445293929, clean diagnostics. |
| `uv run dynamaxx-eval iteration --model dino_ri2m_ekman_depth_orolift_theta --workers 4` | 0 | Primary score -0.13156559713631472, clean diagnostics. |
| `uv run dynamaxx-eval validation --model dino_ri2m_ekman_depth_orolift_theta --workers 4` | 0 | Primary score -0.13341144990707632, clean diagnostics. |

## Repair Attempts

- Failure observed: none after implementation handoff.
- Implementer-owned failure: no
- NaN/Inf forecast observed: no
- Fix attempted: none
- Follow-up command and result: not applicable

## Known Limitations

- Limitation: the terrain forcing is deliberately low-mode, capped, and thermal-only; it does not introduce a momentum-side mountain-wave drag term.
- Limitation: no-op fallback behavior preserves robustness when constants are missing, but it also means deployments without the WeatherBench2 surface geopotential constant receive no orographic-lift effect.

## Rollback Notes

Revert candidate source/test changes by reverting commit `7af558f97f2d1286203664f9d6bac17bb8cacbc0`, or by applying the reverse of `candidate.diff` if the source commit is not available.

# Implementation Record

## Identity

- Proposal slug: `ocean-anchor-ri2m-lower-boundary`
- Candidate model name:
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si_ori`
- Incumbent model name:
  `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si`
- Baseline HEAD: `6f4a63731b2dd7598ef9a6c3c085365ceed7aea9`
- Incumbent source commit: `603f44a9b052557bd3bf3a16a9dcd9c05f343449`
- Candidate commit: `ea124f2d1b43e8e9e54efcbe0abf05e80f6b8001`
- Frozen candidate diff SHA-256:
  `3fedb24a90283f166c29ce487ea4d82f65f58195c75a17f0a441425dbb6a20e3`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

The candidate adds one default-false selector and one side-by-side descendant
of the accepted incumbent. It reuses the existing per-initial-condition ocean
bulk sensible heat-flux anchor without changing its extraction, validation, or
prognostic forcing path.

Output packing records the accepted atmospheric pressure-thickness RI2m result
before applying the incumbent land observer. The candidate then applies the
same bounded skin-aware RI2m routine to the ocean anchor with a unit surface
weight and adds only `1 - land_fraction` of that ocean correction to the
already land-observed result. This gives complementary coastal weights without
double counting and preserves pure-land output exactly.

The existing Richardson algebra, pressure-thickness references, shear floor,
hydrostatic height, stability limiter, `+/-1.5 K` cap, forecast-time ramp,
finite checks, and accepted land observer are reused unchanged. Invalid
anchor, mask, pressure, clock, reference, or geometry cells retain the exact
accepted land result. The atmospheric and skin trajectories, ocean forcing,
residual memory, non-T2m outputs, and public forecast contract are unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k <focused ocean-anchor tests>` | passed | Implementer focused run: 11 passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py -k 'ocean_anchor'` | passed | Orchestrator verification: 13 passed, 273 deselected. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k <related RI2m/land-skin/ocean subset>` | passed | Implementer related run: 33 passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Implementer dependency and registry run: 73 passed. |
| `uv run pytest` | passed | Implementer final full suite: 352 passed, 2 skipped. |
| `uv run ruff check <six changed files>` | passed | Implementer and Orchestrator checks found no lint issues. |
| `git diff --check` | passed | No whitespace errors. |

## Repair Attempts

- Failure observed: none.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none. Formatter-only rewrites to incumbent code were removed
  during scope review before final verification.
- Follow-up result: focused, related, dependency/registry, full-suite, lint,
  and diff checks all passed.

## Known Limitations

- The ocean endpoint is lead-zero 2 m air temperature, not observed sea-surface
  or radiometric skin temperature.
- The accepted ocean forcing already relaxes the lowest atmospheric layer
  toward the same anchor, so the output observer may duplicate existing signal.
- The output-only observer cannot improve MSLP, Z500, U10, or atmospheric
  trajectory errors.

## Rollback Notes

The accepted implementation is retained in source commit
`ea124f2d1b43e8e9e54efcbe0abf05e80f6b8001`. The frozen `candidate.diff`
remains the exact pre-acceptance implementation record. If a later explicit
rollback is required, apply its reverse and verify its SHA-256 before doing so.
The baseline contained only the user-owned untracked `gifs/` directory; it
must not be modified. On rejection, move the ready proposal to
`.logbook/research/scrap/`, leave the ignored history artifacts local, do not
update the leaderboard, and create no commit.

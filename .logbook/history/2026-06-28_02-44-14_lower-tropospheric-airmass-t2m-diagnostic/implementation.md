# Implementation Record

## Identity

- Proposal slug: lower-tropospheric-airmass-t2m-diagnostic
- Candidate model name: dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_airmass
- Incumbent model name: dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m
- Baseline commit: 3992244f20b2a938fdd96f8904f3749f5505670d
- Candidate commit: none; rejected before commit

## Files Changed

- Path: src/dynamaxx/dycore/models/dinosaur/adapter.py
- Path: src/dynamaxx/dycore/models/dinosaur/__init__.py
- Path: src/dynamaxx/dycore/registry.py
- Path: tests/dycore/models/dinosaur/test_primitive_equations.py
- Path: tests/dycore/models/dinosaur/test_dependency.py
- Path: tests/dycore/test_registry.py

## Implementation Summary

Registered a side-by-side Dinosaur candidate derived from the RI2m incumbent.
The candidate added a final-output-only selector that appended hidden
temperature_925, temperature_850, and surface_pressure diagnostics when those
levels were available, then applied a bounded lower-tropospheric air-mass
screen-temperature adjustment after the accepted residual and RI2m paths.

The fixed constants were beta 0.5, smoothstep ramp full at 144 hours, and a
maximum T2m increment of 1.5 K. The implementation preserved the rollout,
forecast contract, non-T2m output channels, and incumbent fallback behavior for
missing pressure levels, missing initial T2m, shape mismatches, or nonfinite
diagnostics.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k 'airmass_t2m or lower_tropospheric_airmass or bulk_richardson_2m_temperature_factory or default_dinosaur_configuration' tests/dycore/models/dinosaur/test_dependency.py -k 'airmass or registered' tests/dycore/test_registry.py -k 'airmass or bulk_richardson'` | passed | 15 passed, 191 deselected |
| `uv run python -m compileall src/dynamaxx/dycore/models/dinosaur src/dynamaxx/dycore/registry.py` | passed | Syntax/import compile check passed |
| `git diff --check` | passed | No whitespace errors |
| `uv run ruff check` | passed | All checks passed |
| `uv run ruff format --check` | failed | Failed only for pre-existing unrelated format drift in src/dynamaxx/dycore/models/dinosaur/primitive_equations.py and src/dynamaxx/eval/device_dispatch.py |
| `uv run ruff format --check <six touched files>` | passed | Six touched files already formatted |
| `uv run pytest` | passed | 272 passed, 2 skipped in 288.60s |
| `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_airmass` | passed | failed=False, issues=0, primary_score=-0.256516760212165 |
| `uv run dynamaxx-eval iteration --model dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_airmass --workers 4` | passed | failed=False, issues=0, primary_score=-0.2527670042476971 |

## Repair Attempts

- Failure observed: none in implementation tests or sanity checks.
- Implementer-owned failure: no.
- NaN/Inf forecast observed: no.
- Fix attempted: none required.
- Follow-up command and result: not applicable.

## Known Limitations

- The candidate worsened T2m skill materially at iteration, so validation was not run.
- The global formatter check still reports unrelated pre-existing drift outside the candidate write scope.

## Rollback Notes

Revert the six source/test files changed by this candidate to HEAD while
preserving the pre-existing untracked gifs/ directory, raw evaluation outputs,
and this history directory.

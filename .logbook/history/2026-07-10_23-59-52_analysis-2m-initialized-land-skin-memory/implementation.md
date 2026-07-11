# Implementation Record

## Identity

- Proposal slug: `analysis-2m-initialized-land-skin-memory`
- Candidate model name: `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri_a2si`
- Incumbent model name: `dino_ri2m_ekman_depth_orolift_lwind_twork_drag_pthick_ri2m_lateskin_skri`
- Baseline HEAD: `07cf68b922784894415df64e36368a60f2df5080`
- Incumbent source commit: `3fb32ff048b00b779d7e16a2c72e728866a4f4ba`
- Candidate commit: `603f44a9b052557bd3bf3a16a9dcd9c05f343449`
- Frozen candidate diff SHA-256: `efba29f26b4ed4145ca6b5b137d52aaff0f9f885c1f528a65500eb6d76bbdef1`

## Files Changed

- `src/dynamaxx/dycore/models/dinosaur/adapter.py`
- `src/dynamaxx/dycore/models/dinosaur/__init__.py`
- `src/dynamaxx/dycore/registry.py`
- `tests/dycore/models/dinosaur/test_dependency.py`
- `tests/dycore/models/dinosaur/test_primitive_equations.py`
- `tests/dycore/test_registry.py`

## Implementation Summary

The candidate adds one default-false selector and one side-by-side registered
descendant of the incumbent. For each initialization, it extracts the causal
lead-zero analyzed 2 m temperature, applies only the existing Kelvin unit
conversion and Dinosaur latitude ordering, and passes it through the private
trajectory closure.

After the incumbent's optional DFI and incumbent lowest-layer skin/deep
initialization, valid active-land cells initialize both hidden reservoirs from
analyzed T2m. Ocean cells, cells below the accepted land threshold, invalid
analysis cells, missing or shape-incompatible analysis fields, and invalid land
masks retain the exact incumbent post-DFI values. The accepted exchange,
observer, masks, caps, constants, and 120-to-240-hour activation ramp are
unchanged. The public forecast input, output, and trajectory-count contracts are
unchanged.

## Tests And Sanity Checks

| Command | Exit Status | Notes |
| --- | --- | --- |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k <focused candidate tests>` | passed | Implementer focused run: 15 candidate tests passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py -k 'analysis_2m'` | passed | Orchestrator verification: 15 passed, 259 deselected. |
| `uv run pytest tests/dycore/models/dinosaur/test_primitive_equations.py -k <related land-skin/residual/ocean/analysis-offset tests>` | passed | Implementer related run: 44 passed. |
| `uv run pytest tests/dycore/models/dinosaur/test_dependency.py tests/dycore/test_registry.py` | passed | Implementer dependency and registry run: 71 passed. |
| `uv run pytest` | passed | Implementer full suite: 340 passed, 2 skipped. |
| `uv run ruff check <six changed files>` | passed | No lint findings. |
| `git diff --check` | passed | No whitespace errors. |

## Repair Attempts

- Failure observed: initial test doubles conflated the private auxiliary carry
  with emitted atmospheric output, and an early-parity test did not place the
  deterministic step exactly at 120 hours.
- Implementer-owned failure: yes, confined to tests.
- NaN/Inf forecast observed: no.
- Fix attempted: separated hidden-carry assertions from atmospheric/output
  assertions and made the deterministic solver land exactly on the accepted
  120-hour boundary.
- Follow-up result: focused, related, dependency/registry, full-suite, lint, and
  diff checks all passed without changing the scientific mechanism.

## Known Limitations

- Analyzed 2 m air temperature is only a proxy for radiometric skin and deep
  soil temperature.
- Both reservoirs use the same analyzed endpoint, intentionally omitting an
  unobserved initial subsurface gradient.
- Candidate effects begin only when the incumbent late ramp activates, so fixed
  iteration scoring is required to determine whether the memory remains useful.

## Rollback Notes

The accepted implementation is retained in source commit
`603f44a9b052557bd3bf3a16a9dcd9c05f343449`. The frozen `candidate.diff`
remains the exact pre-acceptance implementation record.
If a later explicit rollback is required, apply its reverse and verify its
SHA-256 before doing so.
The baseline contained only the user-owned untracked `gifs/` directory; it
must not be modified. On rejection, move the ready proposal to
`.logbook/research/scrap/`, leave the ignored history artifacts local, do not
update the leaderboard, and create no commit.

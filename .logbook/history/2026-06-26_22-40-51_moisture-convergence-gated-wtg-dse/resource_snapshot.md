# Resource Snapshot

- Captured at: 2026-06-26T22:40:51Z
- Repository path: /home/ubuntu/github/kzhao/dynamaxx
- Branch: kzhao--codex
- Baseline commit: ff40def55ac707e8915c840b856a0aaa3345b046
- Incumbent model: dino_hsl2_mass_dse_wtg_vdse_ramp
- Candidate model: dino_hsl2_mass_dse_wtg_vdse_mfcgate
- WeatherBench2 data path: /home/ubuntu/data/weathermaxx-data/weatherbench2/datasets/v1/processed-era5-1p5deg-6h-240x121-equiangular-with-poles-conservative
- Fixed protocols in scope: fast, iteration, validation
- Target variables: 2m_temperature, mean_sea_level_pressure, geopotential_500, 10m_u_component_of_wind
- Lead days: 1..15
- Machine resources before implementation pass: 48 CPUs, 171 GiB RAM available, 4.1T disk free

## Cached Incumbent

- Incumbent commit: ff40def55ac707e8915c840b856a0aaa3345b046
- Iteration primary score: -0.2197104515448394
- Validation primary score: -0.21940899263836755
- Iteration JSON: outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.json
- Iteration CSV: outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_ramp.csv
- Validation JSON: outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.json
- Validation CSV: outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_ramp.csv
- Cache validity: valid. Candidate source edits do not alter the incumbent commit, WeatherBench2 data path, fixed protocols, target variables, lead range, or evaluation gate definitions recorded in `.logbook/leaderboard.json`.

## Pre-Scoring Worktree

Tracked modified files:

- src/dynamaxx/dycore/models/dinosaur/__init__.py
- src/dynamaxx/dycore/models/dinosaur/adapter.py
- src/dynamaxx/dycore/registry.py
- tests/dycore/models/dinosaur/test_dependency.py
- tests/dycore/models/dinosaur/test_primitive_equations.py
- tests/dycore/test_registry.py

Untracked files:

- gifs/ (pre-existing, unrelated, preserved)

## Candidate Fast Gate

- Command: `uv run dynamaxx-eval fast --model dino_hsl2_mass_dse_wtg_vdse_mfcgate`
- Exit status: 0
- Diagnostics failed: false
- Diagnostics issue count: 0
- Records: 120
- Primary score: -0.22390463383670187
- Metrics JSON: outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_mfcgate.json
- Metrics CSV: outputs/eval/fast_dino_hsl2_mass_dse_wtg_vdse_mfcgate.csv

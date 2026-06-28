# Scoring Notes

## Gate Status

- Registration: candidate `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m_eady_hfx` and incumbent `dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m` both instantiated through `create_dycore_model`.
- Full test suite: `uv run pytest` passed with 272 passed and 2 skipped in 311.17s.
- Fast gate: reused the existing candidate fast artifact. It was readable, finite, diagnostics-clean, had 120 records, and primary score `-0.21702676229647105`.
- Iteration: candidate primary score was `-0.21288078610169414`; cached incumbent iteration primary score was `-0.21299732605547173`; delta was `+0.00011653995377758353`.
- Iteration promotion gate: did not promote. Diagnostics were clean and RMSE guardrails passed, but the primary delta was below the required `+0.002`.
- Validation: skipped, as required by the protocol and user instruction, because iteration did not promote.
- Golden: not run.

## Guardrails

- Early day 1-5 mean RMSE regressions all passed the fixed `2%` threshold:
  - `10m_u_component_of_wind`: `-0.00000003016618605816181%`
  - `2m_temperature`: `+0.0000000375381304233521%`
  - `geopotential_500`: `+0.000000024975671860730422%`
  - `mean_sea_level_pressure`: `+0.000000019099881875944207%`
- Worst single variable-lead RMSE regression passed the fixed `10%` threshold:
  - `2m_temperature` at 48 h, `+0.0000002497315654025058%`

## Cache Reuse

- Incumbent was not rerun.
- Iteration incumbent artifacts reused:
  - JSON: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m.json`
  - CSV: `outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m.csv`
- Validation incumbent artifacts checked and retained for reference but not used for a candidate validation comparison:
  - JSON: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m.json`
  - CSV: `outputs/eval/validation_dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m.csv`
- Cache checks performed: requested incumbent matched `.logbook/leaderboard.json`, `HEAD` matched leaderboard `eval_code_commit`, leaderboard protocols included `iteration` and `validation`, artifacts were readable, primary scores were finite, diagnostics were clean, and iteration records covered the fixed target variables and lead hours needed for guardrail comparison.

## Anomalies

- The candidate iteration run was long but progressed steadily with 4 effective GPU workers and completed successfully.
- No failed or restarted scoring commands.
- No nonfinite, malformed, or diagnostic-failed evaluation artifacts were observed.
- Candidate validation was not run because the fixed iteration promotion gate failed.

## Measurement Lessons

- The Eady-limited heat-flux candidate is effectively neutral against the incumbent on fixed iteration: it improves primary score by only `+0.00011653995377758353`, below promotion threshold, and leaves early-lead RMSE guardrails nearly unchanged.
- The clean but tiny movement suggests this implementation strength or placement is too weak to matter materially under the fixed iteration protocol, rather than numerically unstable.

## Recommendation To Orchestrator

Do not promote this candidate to validation under the fixed gate. This is a measurement recommendation only; the Orchestrator should decide whether to reject or revise the candidate.

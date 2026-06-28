# Scoring Notes

## Gate Status

- Fast gate: passed; candidate failed=False, issues=0, primary_score=-0.256516760212165.
- Iteration promotion gate: failed; candidate primary_score=-0.2527670042476971 versus cached incumbent primary_score=-0.21299732605547173, delta=-0.03976967819222538.
- Validation acceptance gate: not run because iteration did not promote.

## Measurement Lessons

- The lower-tropospheric air-mass T2m blend worsened the already difficult T2m channel rather than improving it.
- The failure is concentrated in T2m: mean T2m skill delta was -0.07953923723642987 and the largest RMSE regression was 0.6870379845394492 K at 144 h.
- Non-T2m channels stayed effectively unchanged, with only numerical-noise-level metric movement.
- Future T2m work should avoid another final-output blend unless it includes a stronger physical constraint or is first studied as a read-only diagnostic.

## Anomalies

- Cache reuse: incumbent iteration metrics were reused from outputs/eval/iteration_dino_hsl2_mass_dse_wtg_vdse_t2m_lomem_ri2m.json and .csv; no incumbent rerun was performed.
- Resource limits: none observed. Iteration used workers=4 on four GPUs after resource check showed adequate RAM, GPU memory, CPU capacity, and disk.
- Failed or restarted commands: global `uv run ruff format --check` failed only because of unrelated pre-existing format drift outside the six touched candidate files.
- Nonfinite or unstable outputs: none observed; fast and iteration diagnostics reported failed=False and issues=[].

## Recommendation To Orchestrator

Reject the candidate. It ran cleanly but failed the fixed iteration promotion
gate by a large negative primary-score delta, so validation should remain
unrun and the candidate source/test changes should be reverted.

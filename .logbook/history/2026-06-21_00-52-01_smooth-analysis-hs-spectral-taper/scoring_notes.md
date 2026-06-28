# Scoring Notes

## Gate Status

- Fast gate: passed. Candidate `fast` completed with `failed=False`, `issues=0`, and primary score `-0.5300238923013832`.
- Iteration promotion gate: failed. Candidate iteration score was `-0.5146503692452032` versus cached incumbent `-0.5150627015910243`, for delta `+0.0004123323458210537`, below the required `+0.002`.
- Validation acceptance gate: not run. Validation is not allowed when iteration does not promote.

## Measurement Lessons

- The smooth analysis-HS taper was numerically clean and produced small RMSE improvements across all fixed target variables and leads checked, but the aggregate primary-score gain was too small for promotion.
- The hard analysis-HS cutoff may not be a material remaining error source, or the raised-cosine change is too small to clear the conservative promotion threshold.
- The candidate is useful negative evidence because it isolated the horizontal spectral taper without changing the accepted offset source state, rate, vertical projection, or lead persistence.

## Anomalies

- Cache reuse: incumbent iteration and validation metrics were reused from `.logbook/leaderboard.json` artifacts. No incumbent evaluation was run.
- Resource limits: none. Candidate iteration used `--workers 4`.
- Failed or restarted commands: the Implementer recorded an earlier candidate fast JIT failure and repair. The Scorer reran full pytest, candidate fast, and candidate iteration successfully.
- Nonfinite or unstable outputs: none observed; candidate diagnostics had zero issues.

## Recommendation To Orchestrator

Measured gate status is rejection under the fixed protocol: diagnostics and
RMSE guardrails are clean, but the iteration primary-score delta is below the
required `+0.002`, so validation should remain skipped and the candidate should
not replace the incumbent.

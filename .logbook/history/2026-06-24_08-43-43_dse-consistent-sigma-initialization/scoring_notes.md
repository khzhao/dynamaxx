# Scoring Notes

## Gate Status

- Fast gate: passed. `uv run dynamaxx-eval fast --model dino_mass_dse_init` exited 0 with `failed=false`, 0 issues, 120 records, and primary score `-0.26307357364618555`.
- Iteration promotion gate: did not promote. Candidate iteration primary score was `-0.26271419693216724` versus cached incumbent `-0.2616483974683927`, for delta `-0.0010657994637745527`; the required promotion delta is `>= +0.002`.
- Iteration diagnostics and guardrails: clean diagnostics, early day 1-5 mean RMSE regression `-0.6345484837916622%` against the `<= 2%` guardrail, and worst variable+lead RMSE regression `1.9422206593772608%` against the `<= 10%` guardrail.
- Validation acceptance gate: not run. The fixed workflow only permits candidate validation after iteration promotion.
- Golden: not run.

## Cache Reuse

- Iteration incumbent metrics were reused from the leaderboard cache: `outputs/eval/iteration_dino_hsl2_mass_dse.json` and `outputs/eval/iteration_dino_hsl2_mass_dse.csv`.
- Cache checks passed: requested incumbent equals leaderboard incumbent, fingerprint is compatible for iteration, leaderboard `eval_code_commit` matches current HEAD `2c70bb5b77370a074330c2b46954f74f20771f12`, cached artifacts are readable, primary score is finite, diagnostics are clean, and all 60 incumbent model variable/lead records needed for guardrails are present.
- Validation incumbent metrics were available at `outputs/eval/validation_dino_hsl2_mass_dse.json` and `.csv` with primary `-0.2600180396322455`, but were not used because candidate validation was skipped.
- Candidate source edits in the current dirty worktree were not treated as cache invalidation, per `roles/SCORER.md`.

## Measurement Lessons

- The DSE-consistent sigma initialization remained numerically clean but did not improve the fixed iteration primary score.
- Early-lead RMSE moved favorably on 10 m zonal wind, 2 m temperature, and mean sea level pressure, but early geopotential_500 worsened by `0.8815813122977961%` on average and the net primary score regressed.
- The largest RMSE regression was geopotential_500 at 24 h: candidate `250.68050470361348` versus incumbent `245.90449676510394`, a `1.9422206593772608%` regression.

## Anomalies

- Resource limits: no resource failures. The candidate iteration run used `--workers 4`; a non-invasive status check during the run showed four worker Python processes active and all four GPUs at 100% utilization.
- Failed or restarted commands: none.
- Nonfinite or unstable outputs: none observed.
- Runtime behavior: fast and iteration were quiet for long intervals while computing, but continued to emit chunk completions and exited 0.
- Worktree note: unrelated untracked `gifs/` was ignored.

## Recommendation To Orchestrator

Report the measured gate status: iteration did not promote to validation because the primary-score delta was negative. This is a measurement report only; no accept/reject decision is made by the Scorer.

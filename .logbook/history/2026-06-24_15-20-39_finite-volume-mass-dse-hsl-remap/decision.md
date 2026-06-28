# Decision Record

## Decision

`rejected`

## Score Summary

- Iteration candidate primary score: `-0.26214561232546824`
- Iteration incumbent primary score: `-0.2616483974683927`
- Iteration delta: `-0.0004972148570755452`
- Validation candidate primary score: not run
- Validation incumbent primary score: `-0.2600180396322455`
- Validation delta: not applicable

## Rationale

The candidate passed full unit tests, fast, iteration diagnostics, and both
fixed RMSE guardrails, but failed the primary iteration promotion gate. The
cached incumbent iteration artifact for `dino_hsl2_mass_dse` was valid and was
reused; no incumbent rerun was warranted. Candidate iteration scored
`-0.26214561232546824`, which is `-0.0004972148570755452` below the cached
incumbent score and below the required `+0.002` improvement.

The guardrails were clean. The worst early day-1-to-5 mean RMSE regression was
`+0.061352004162448404%` for `2m_temperature`, below the `2%` threshold. The
worst variable-lead RMSE regression was `+0.09484825576416078%` for
`2m_temperature` at 312 hours, below the `10%` threshold. Validation was skipped
because the primary iteration gate failed. Golden was not run.

## Lessons Learned

- A global quadrature-conserving correction to the mass-DSE HSL remap is stable
  and guardrail-clean but does not improve the fixed primary score.
- The accepted bilinear HSL2 mass-DSE remap remains slightly better than the
  conservative global-integral correction under the iteration metric.
- Future remap proposals need either local conservation without extra diffusion
  or a stronger mechanism than global integral preservation, especially given
  the added runtime cost.

## Cleanup Completed

- Candidate code retained or reverted: reverted using
  `.logbook/history/2026-06-24_15-20-39_finite-volume-mass-dse-hsl-remap/candidate.diff`
- Research state updated: removed
  `.logbook/research/ready/finite-volume-mass-dse-hsl-remap.md`
- Leaderboard updated: no, rejected candidate
- Git status checked: tracked files clean; pre-existing untracked `gifs/`
  directory preserved

## Next Action

Start the next continuous-loop iteration by generating and triaging new
Researcher proposals against the cached `dino_hsl2_mass_dse` incumbent.

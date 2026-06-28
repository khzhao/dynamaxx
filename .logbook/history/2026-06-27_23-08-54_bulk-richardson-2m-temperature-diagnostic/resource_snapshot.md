# Resource Snapshot

## Resource Check

- Timestamp: 2026-06-27T23:08:55Z
- CPU count: 48
- Available RAM: 171 GiB
- GPU count: 4
- GPU memory free before scoring: NVIDIA L4 GPUs 0-3 each reported 22566 MiB free of 23034 MiB
- Repository/output free disk: 4.1 TiB on `/dev/root`
- Selected worker count: 4

## Rationale

The machine had more than 128 GiB available RAM, four visible L4 GPUs with most memory free, and far more than the required 50 GiB free disk. `--workers 4` matches the protocol's conservative cap for this resource tier and stayed below half of the 48 CPU cores.

## Git State

- Baseline commit before implementation: `d1f132fafcad09bcc92cfeedbe3fc2be1b930770`
- Pre-existing user-owned untracked path preserved: `gifs/`
- Accepted candidate commit: `3992244f20b2a938fdd96f8904f3749f5505670d`
- Incumbent metrics reused from `.logbook/leaderboard.json`; no incumbent evaluation was rerun.

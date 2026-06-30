# Resource Snapshot

- Created at: 2026-06-29T21:03:42Z
- Proposal slug: static-roughness-weighted-ekman-coupling
- Candidate model name: dino_ri2m_ekman_z0
- Incumbent model name: dino_ri2m_ekman_coupled
- Baseline commit: d35078e83314b8ef70f0d8a23f9765e03ed3750e
- Baseline git status: clean tracked worktree; pre-existing untracked `gifs/` ignored and protected from rollback.
- CPU count: 48
- Available RAM: approximately 170 GiB
- GPU inventory: 4 x NVIDIA L4, approximately 22.5 GiB free of 23.0 GiB each
- Disk free: approximately 4.1 TiB on repository, outputs, and logbook filesystem
- Selected evaluation workers: 4
- Worker rationale: below half of 48 CPU cores, allowed by available RAM above 128 GiB, with ample disk and GPU memory.
- Incumbent cache: reuse `.logbook/leaderboard.json` artifacts for `dino_ri2m_ekman_coupled`; do not rerun incumbent unless concretely invalid.

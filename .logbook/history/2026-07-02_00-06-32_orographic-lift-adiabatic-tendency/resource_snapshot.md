# Resource Snapshot

- Recorded at: 2026-07-02T00:06:32Z
- Proposal slug: orographic-lift-adiabatic-tendency
- Candidate model: dino_ri2m_ekman_depth_orolift_theta
- Incumbent model: dino_ri2m_ekman_depth
- Baseline commit: a77f88ef63161f2ac50f663f2ab6a53f5a1b42c0
- Branch: kzhao--more-opt
- Baseline git status:
  ?? gifs/
- CPU count: 48
- MemAvailable: 178282120 kB
- Disk free: 4.1T available on /dev/root
- Output disk free: 4.1T available on /dev/root
- GPU status:
  0, NVIDIA L4, 22566 MiB, 23034 MiB
  1, NVIDIA L4, 22566 MiB, 23034 MiB
  2, NVIDIA L4, 22566 MiB, 23034 MiB
  3, NVIDIA L4, 22566 MiB, 23034 MiB
- Selected workers: 4
- Worker rationale: 48 CPUs, ~178 GiB available RAM, 4 L4 GPUs with ~22.5 GiB free each, and >50 GiB free disk.
- Incumbent cache: reuse .logbook/leaderboard.json pointers unless concrete invalidation is found.

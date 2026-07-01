# Resource Snapshot

- Timestamp: `2026-07-01T03:35:20Z`
- Proposal slug: `coriolis-scaled-ekman-depth-coupling`
- Selected model name: `dino_ri2m_ekman_depth`
- Incumbent model: `dino_ri2m_ekman_coupled`
- Incumbent accepted commit: `d187308d30a242bf38aabe5b7eb530fca522a68f`
- Baseline HEAD: `2d592c9fb419a0a157fd6d0b8cba8ff862bdfc46`
- Cached incumbent iteration primary score: `-0.16500618979404214`
- Cached incumbent validation primary score: `-0.16591150807771451`
- Cached iteration artifact: `outputs/eval/iteration_dino_ri2m_ekman_coupled.json`
- Cached validation artifact: `outputs/eval/validation_dino_ri2m_ekman_coupled.json`
- Worker policy: `--workers 4`; resources support 4 workers and this matches prior fixed-gate runs.
- Commit policy: commit only if accepted; rejected implementation changes must be reverted and rejected logbook artifacts are not committed.

## Baseline Git Status

```text
## kzhao--more-opt
 D .logbook/research/staging/coriolis-scaled-ekman-depth-coupling.md
?? gifs/
```

## Resources

```text
48
               total        used        free      shared  buff/cache   available
Mem:           181Gi        11Gi        38Gi       3.7Mi       132Gi       170Gi
Swap:             0B          0B          0B
Filesystem      Size  Used Avail Use% Mounted on
/dev/root       4.8T  707G  4.1T  15% /
/dev/root       4.8T  707G  4.1T  15% /
0, NVIDIA L4, 22566 MiB, 23034 MiB
1, NVIDIA L4, 22566 MiB, 23034 MiB
2, NVIDIA L4, 22566 MiB, 23034 MiB
3, NVIDIA L4, 22566 MiB, 23034 MiB
```

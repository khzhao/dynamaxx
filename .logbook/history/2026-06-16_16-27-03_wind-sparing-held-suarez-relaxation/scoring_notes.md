# Scoring Notes

Candidate model: `dinosaur_dfi_surface_residual_weak_hs`

Incumbent model: `dinosaur_dfi_surface_residual`

Generated at: `2026-06-16T17:32:25Z`

Repository commit: `845de671268f42c6b44b0a60c287e043087364a1`

## Command Record

- Read role instructions:
  - `sed -n '1,240p' roles/PROTOCOL.md` exited 0.
  - `sed -n '1,260p' roles/SCORER.md` exited 0.
- Confirmed registry references:
  - `rg "dinosaur_dfi_surface_residual(_weak_hs)?" src/dynamaxx/dycore -n` exited 0.
  - The first registry API probe below exited 1 because the registry API is `create_dycore_model`, not `get_model`; no source files were changed.

```bash
uv run python - <<'PY'
from dynamaxx.dycore.registry import get_model
for model_name in ['dinosaur_dfi_surface_residual', 'dinosaur_dfi_surface_residual_weak_hs']:
    model = get_model(model_name)
    print(model_name, 'registered', model.name)
PY
```

  - The corrected registry check below exited 0 and created both `dinosaur_dfi_surface_residual` and `dinosaur_dfi_surface_residual_weak_hs`.

```bash
uv run python - <<'PY'
from dynamaxx.dycore.registry import create_dycore_model, dycore_model_names
required_names = ['dinosaur_dfi_surface_residual', 'dinosaur_dfi_surface_residual_weak_hs']
registered_names = dycore_model_names()
print('registered_names', registered_names)
for model_name in required_names:
    model = create_dycore_model(model_name)
    print(model_name, 'created_name', model.name)
PY
```

- Test status:
  - `uv run pytest` was not rerun by Scorer because the Orchestrator supplied a passing full pytest record: exit 0, 103 passed, 2 skipped.
  - `golden` was not run.
- Fast gate verification:
  - The command below exited 0.

```bash
python - <<'PY'
import json
from pathlib import Path
candidate_name = 'dinosaur_dfi_surface_residual_weak_hs'
path = Path('outputs/eval/fast_dinosaur_dfi_surface_residual_weak_hs.json')
data = json.loads(path.read_text())
rows = [record for record in data['records'] if record.get('model_name') == candidate_name]
assert data['model_name'] == candidate_name
assert data['diagnostics']['failed'] is False
assert len(data['diagnostics']['issues']) == 0
assert len(rows) == 60
print('fast_gate_verified', path, data['primary_score'], 'issues', len(data['diagnostics']['issues']), 'filtered_records', len(rows))
PY
```

  - Candidate fast primary: `-1.1909821759396455`; diagnostics failed: `false`; issue count: `0`; filtered candidate records: `60`.
- Candidate iteration:
  - `uv run dynamaxx-eval iteration --model dinosaur_dfi_surface_residual_weak_hs --workers 4` exited 0.
  - Output JSON: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs.json`
  - Output CSV: `outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs.csv`
- Iteration comparison:
  - The command below exited 0.

```bash
python - <<'PY'
import json
from pathlib import Path
candidate_path=Path('outputs/eval/iteration_dinosaur_dfi_surface_residual_weak_hs.json')
incumbent_path=Path('outputs/eval/iteration_dinosaur_dfi_surface_residual.json')
candidate_name='dinosaur_dfi_surface_residual_weak_hs'
incumbent_name='dinosaur_dfi_surface_residual'

def load(path, model_name):
    data=json.loads(path.read_text())
    rows=[r for r in data['records'] if r.get('model_name') == model_name]
    return data, rows

cand, cand_rows=load(candidate_path, candidate_name)
inc, inc_rows=load(incumbent_path, incumbent_name)
print('candidate_primary', repr(cand['primary_score']))
print('incumbent_primary', repr(inc['primary_score']))
print('primary_delta', repr(cand['primary_score'] - inc['primary_score']))
print('candidate_diag_failed', cand['diagnostics'].get('failed'), 'issues', len(cand['diagnostics'].get('issues', [])))
print('incumbent_diag_failed', inc['diagnostics'].get('failed'), 'issues', len(inc['diagnostics'].get('issues', [])))
print('filtered_records', len(cand_rows), len(inc_rows))

inc_by_key={(r['variable'], r['lead_hours']): r for r in inc_rows}
cand_by_key={(r['variable'], r['lead_hours']): r for r in cand_rows}
keys=sorted(set(inc_by_key) & set(cand_by_key), key=lambda k: (k[0], k[1]))
print('matched_keys', len(keys))
print('\nearly_mean_rmse_regressions')
for variable in sorted({k[0] for k in keys}):
    early=[k for k in keys if k[0] == variable and k[1] <= 120]
    cand_mean=sum(cand_by_key[k]['rmse'] for k in early)/len(early)
    inc_mean=sum(inc_by_key[k]['rmse'] for k in early)/len(early)
    rel=(cand_mean-inc_mean)/inc_mean
    print(variable, 'cand', repr(cand_mean), 'inc', repr(inc_mean), 'rel', repr(rel))

print('\nmax_variable_lead_rmse_regressions')
for variable in sorted({k[0] for k in keys}):
    vals=[]
    for k in keys:
        if k[0] == variable:
            rel=(cand_by_key[k]['rmse']-inc_by_key[k]['rmse'])/inc_by_key[k]['rmse']
            vals.append((rel,k,cand_by_key[k]['rmse'],inc_by_key[k]['rmse']))
    rel,k,c_rmse,i_rmse=max(vals, key=lambda x: x[0])
    print(variable, 'lead_hours', k[1], 'cand', repr(c_rmse), 'inc', repr(i_rmse), 'rel', repr(rel))
print('\nglobal_max')
vals=[]
for k in keys:
    rel=(cand_by_key[k]['rmse']-inc_by_key[k]['rmse'])/inc_by_key[k]['rmse']
    vals.append((rel,k,cand_by_key[k]['rmse'],inc_by_key[k]['rmse']))
print(max(vals, key=lambda x: x[0]))
PY
```

  - Incumbent JSON reused: `outputs/eval/iteration_dinosaur_dfi_surface_residual.json`
  - Incumbent CSV reused: `outputs/eval/iteration_dinosaur_dfi_surface_residual.csv`
- Candidate validation:
  - `uv run dynamaxx-eval validation --model dinosaur_dfi_surface_residual_weak_hs --workers 4` exited 0.
  - Output JSON: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs.json`
  - Output CSV: `outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs.csv`
- Validation comparison:
  - The command below exited 0.

```bash
python - <<'PY'
import json
from pathlib import Path

def summarize(case, candidate_path, incumbent_path, candidate_name, incumbent_name):
    cand=json.loads(Path(candidate_path).read_text())
    inc=json.loads(Path(incumbent_path).read_text())
    cand_rows=[r for r in cand['records'] if r.get('model_name') == candidate_name]
    inc_rows=[r for r in inc['records'] if r.get('model_name') == incumbent_name]
    inc_by_key={(r['variable'], r['lead_hours']): r for r in inc_rows}
    cand_by_key={(r['variable'], r['lead_hours']): r for r in cand_rows}
    keys=sorted(set(inc_by_key) & set(cand_by_key), key=lambda k: (k[0], k[1]))
    print('\nCASE', case)
    print('candidate_primary', repr(cand['primary_score']))
    print('incumbent_primary', repr(inc['primary_score']))
    print('primary_delta', repr(cand['primary_score'] - inc['primary_score']))
    print('candidate_diag_failed', cand['diagnostics'].get('failed'), 'issues', len(cand['diagnostics'].get('issues', [])))
    print('incumbent_diag_failed', inc['diagnostics'].get('failed'), 'issues', len(inc['diagnostics'].get('issues', [])))
    print('filtered_records', len(cand_rows), len(inc_rows), 'matched_keys', len(keys))
    print('early_mean_rmse_regressions')
    for variable in sorted({k[0] for k in keys}):
        early=[k for k in keys if k[0] == variable and k[1] <= 120]
        cand_mean=sum(cand_by_key[k]['rmse'] for k in early)/len(early)
        inc_mean=sum(inc_by_key[k]['rmse'] for k in early)/len(early)
        rel=(cand_mean-inc_mean)/inc_mean
        print(variable, repr(cand_mean), repr(inc_mean), repr(rel))
    print('max_variable_lead_rmse_regressions')
    global_vals=[]
    for variable in sorted({k[0] for k in keys}):
        vals=[]
        for k in keys:
            if k[0] == variable:
                rel=(cand_by_key[k]['rmse']-inc_by_key[k]['rmse'])/inc_by_key[k]['rmse']
                vals.append((rel,k,cand_by_key[k]['rmse'],inc_by_key[k]['rmse']))
                global_vals.append((rel,k,cand_by_key[k]['rmse'],inc_by_key[k]['rmse']))
        rel,k,c_rmse,i_rmse=max(vals, key=lambda x: x[0])
        print(variable, k[1], repr(c_rmse), repr(i_rmse), repr(rel))
    print('global_max', max(global_vals, key=lambda x: x[0]))

candidate='dinosaur_dfi_surface_residual_weak_hs'
incumbent='dinosaur_dfi_surface_residual'
summarize('validation', 'outputs/eval/validation_dinosaur_dfi_surface_residual_weak_hs.json', 'outputs/eval/validation_dinosaur_dfi_surface_residual.json', candidate, incumbent)
PY
```

  - Incumbent JSON reused: `outputs/eval/validation_dinosaur_dfi_surface_residual.json`
  - Incumbent CSV reused: `outputs/eval/validation_dinosaur_dfi_surface_residual.csv`

Additional read-only inspection commands checked artifact existence, JSON schema, leaderboard pointers, git status, and UTC timestamp. These did not modify source code.

## Iteration Gate

- Candidate primary: `-1.2218408656785489`
- Incumbent primary: `-1.2854136202685928`
- Primary delta: `0.06357275459004397`
- Required delta: `>= 0.002`
- Candidate diagnostics failed: `false`
- Candidate diagnostic issue count: `0`
- Incumbent diagnostics failed: `false`
- Incumbent diagnostic issue count: `0`
- Filtered records compared: candidate `60`, incumbent `60`
- Gate status: `passed`

Early mean RMSE regressions, leads day 1-5:

| Variable | Candidate mean RMSE | Incumbent mean RMSE | Relative regression | Guardrail |
| --- | ---: | ---: | ---: | --- |
| 10 m zonal wind | 9.25692289266928 | 9.191500982911077 | 0.00711765247915837 | pass |
| 2 m temperature | 7.401365301163406 | 7.807050586677929 | -0.0519639627040191 | pass |
| 500 hPa geopotential | 771.9761195101368 | 766.5217952826715 | 0.007115680546896694 | pass |
| Mean sea level pressure | 1050.7180420326392 | 1057.7060920239628 | -0.0066067975253424754 | pass |

Max variable+lead RMSE regressions:

| Variable | Lead hours | Candidate RMSE | Incumbent RMSE | Relative regression | Guardrail |
| --- | ---: | ---: | ---: | ---: | --- |
| 10 m zonal wind | 360 | 16.06252280327027 | 14.894407183172081 | 0.07842645939060551 | pass |
| 2 m temperature | 24 | 3.8084913013000303 | 3.9359464533707373 | -0.03238233893186089 | pass |
| 500 hPa geopotential | 360 | 2266.24510748178 | 2163.5952734093744 | 0.04744410164598433 | pass |
| Mean sea level pressure | 360 | 2949.4052735575247 | 2918.5338950208447 | 0.010577700875548483 | pass |

Global max variable+lead regression: `10 m zonal wind`, lead `360` hours, relative regression `0.07842645939060551`.

## Validation Gate

- Candidate primary: `-1.2103467803549615`
- Incumbent primary: `-1.2725740410982802`
- Primary delta: `0.062227260743318746`
- Required delta: `>= 0.001`
- Candidate diagnostics failed: `false`
- Candidate diagnostic issue count: `0`
- Incumbent diagnostics failed: `false`
- Incumbent diagnostic issue count: `0`
- Filtered records compared: candidate `60`, incumbent `60`
- Gate status: `passed`

Early mean RMSE regressions, leads day 1-5:

| Variable | Candidate mean RMSE | Incumbent mean RMSE | Relative regression | Guardrail |
| --- | ---: | ---: | ---: | --- |
| 10 m zonal wind | 9.167337626773287 | 9.103037140161696 | 0.007063630041440115 | pass |
| 2 m temperature | 7.415471109401864 | 7.808178235159573 | -0.05029433421350225 | pass |
| 500 hPa geopotential | 752.6338123268208 | 747.4524892539072 | 0.0069319764766393914 | pass |
| Mean sea level pressure | 1019.2888356566452 | 1026.6591818905158 | -0.007178961006610429 | pass |

Max variable+lead RMSE regressions:

| Variable | Lead hours | Candidate RMSE | Incumbent RMSE | Relative regression | Guardrail |
| --- | ---: | ---: | ---: | ---: | --- |
| 10 m zonal wind | 360 | 15.930163311813633 | 14.715684166858019 | 0.08252957396916741 | pass |
| 2 m temperature | 24 | 3.8324065044688616 | 3.9556390195570246 | -0.031153630166678686 | pass |
| 500 hPa geopotential | 360 | 2240.315950075878 | 2138.0691430058973 | 0.04782203017355767 | pass |
| Mean sea level pressure | 360 | 2892.7684971463223 | 2863.30142050353 | 0.01029129396988534 | pass |

Global max variable+lead regression: `10 m zonal wind`, lead `360` hours, relative regression `0.08252957396916741`.

## Cache And Resource Notes

- Candidate iteration reported `chunks=229 cached=0 pending=229` and completed all chunks.
- Candidate validation reported `chunks=46 cached=0 pending=46` and completed all chunks.
- Both candidate evals reported `mode=gpu requested_workers=4 effective_workers=4 gpu_count=4 worker_devices=0:0,1:1,2:2,3:3`.
- No command failures occurred in the fixed candidate evaluation commands.
- No resource warnings, hangs, diagnostic failures, or diagnostic issues were reported.

## Measurement Lessons

- Evaluation artifacts include persistence rows, so candidate and incumbent comparisons must filter records by exact `model_name`.
- The largest RMSE regression appears consistently in long-lead `10 m zonal wind`, while the primary score improves substantially on both iteration and validation.
- The candidate iteration and validation metrics came from fresh uncached runs, which is useful for future reproducibility checks.

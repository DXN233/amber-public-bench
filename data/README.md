# Data layout (replaceable)

This harness reads **any** directory that follows the layout below.
The fair-rerun pack under `reference/fair_r2/` is only a **reference fixture**
(published numbers + full task bank). It is not the only path.

## Required layout

```
<data-dir>/
  tasks/
    daily50.jsonl      # one JSON object per line; fields: id, track, prompt, gold, ...
    prog30.jsonl       # prog rows also need ctx_b / ctx_c relative paths
    lit20.jsonl        # lit rows may include amber_snippet
  corpus/
    daily_ledger.txt   # FACT|... lines (NOISE|/HIST| ignored if present)
    lit_fullctx.txt    # concatenated paper windows for B_fullctx
  contexts/prog/       # only for programming track
    P01_B.txt
    P01_C.txt
    ...
  params/              # optional overrides (run_params.json)
  raw/                 # written by run_bench.py
  results/             # written by summarize.py
```

Filenames `daily50` / `prog30` / `lit20` are historical; counts may be smaller
(see `data/sample_minimal/`).

## Use the sample

```bash
export AMBER_DATA_DIR=data/sample_minimal
# plus AMBER_* / UPSTREAM_* from .env.example
python3 scripts/run_bench.py --backend amber --repeats 1
python3 scripts/summarize.py --data-dir data/sample_minimal
```

## Bring your own data

1. `cp -r data/sample_minimal data/my_corp`
2. Edit `corpus/daily_ledger.txt` and `tasks/*.jsonl`
3. For prog: drop your own `contexts/prog/*_{B,C}.txt` and point `ctx_b`/`ctx_c`
4. `export AMBER_DATA_DIR=data/my_corp`
5. If measuring a **real** AMBER tenant, also **import the same corpus into AMBER**
   (tenant ingest / memory write API of your deployment). The C arm sends the
   question only; retrieval happens inside AMBER.

### Task JSONL schema (minimal)

```json
{"id":"D01","track":"daily","prompt":"...","gold":{"must_any":["..."],"abstain":false}}
```

Prog locate example:

```json
{"id":"P01","track":"prog","prompt":"...","gold":{"mode":"locate","must_any":["1600"],"must_file_any":["constants.py"]},
 "ctx_b":"contexts/prog/P01_B.txt","ctx_c":"contexts/prog/P01_C.txt"}
```

## Do not run `build_tasks.py`

It rebuilds from private sandboxes that are **not** in this repo and is refused
unless `FORCE_REBUILD=1` (maintainers only).

# AMBER public comparison bench

**Public harness to measure a memory layer — not the memory product source code.**

Connect your AMBER (OpenAI-compatible) endpoint, swap in your own corpus/tasks, and
compare three arms: no-memory / full-context dump / memory-on.

> **Published reference (fair rerun r2, local protocol simulation → upstream):**
> daily **9.3×** · programming **15.2×** · literature **10.6×**
> (B_fullctx ÷ C_amber prompt tokens). See `reference/fair_r2/`.
> That pack is a **fixture**, not the only way to run this repo.

## What this repo is / is not

| Is | Is not |
|---|---|
| Reproducible **comparison harness** | The AMBER memory service itself |
| Client that talks to an OpenAI-compatible **AMBER** API | A local re-implementation of retrieval sold as “our product” |
| Replaceable `data/` + reference fixture | A single hard-coded Grok/ledger demo |

## Results snapshot (reference fixture)

From `reference/fair_r2/` — backend **local_sim**, same upstream model, 100 tasks × 3 arms × 3 repeats = **900** calls:

| Track | Tasks | B÷C prompt | C completion rate (protocol) |
|------|------:|----------:|-----------------------------:|
| daily | 50 | **9.33×** | 0.980 |
| prog | 30 | **15.23×** | 0.700 |
| lit | 20 | **10.61×** | 1.000 |

Main table = protocol scores (`human_score` column left empty).  
Honest limits: see `ERRATA.md` / `METHOD.md`. Do **not** advertise the retracted v1 daily **236×**.

## Two-step main path

### 1) Connect AMBER (memory layer)

```bash
cp .env.example .env
# set:
#   AMBER_BASE_URL=https://YOUR_HOST/v1
#   AMBER_API_KEY=...
#   UPSTREAM_API_KEY=...          # for A_plain + B_fullctx baseline
#   AMBER_DATA_DIR=data/sample_minimal   # start small
```

Memory on/off contract (pick what your gateway supports):

- Env: `AMBER_MEMORY=on|off`
- Header: `X-AMBER-Memory: on|off` (names overridable in `.env`)
- Or dual base URLs: `AMBER_BASE_URL_MEMORY_ON` / `AMBER_BASE_URL_MEMORY_OFF`

```bash
python3 scripts/run_bench.py --backend amber --data-dir data/sample_minimal --repeats 1
python3 scripts/summarize.py --data-dir data/sample_minimal
```

**Arm mapping (amber backend):**

| Arm | Meaning |
|-----|---------|
| `A_plain` | Question only → upstream (or AMBER with memory OFF) |
| `B_fullctx` | Full corpus injected client-side → upstream (naive dump baseline) |
| `C_amber` | Question only → **AMBER with memory ON** (retrieval inside the service) |

Import the same corpus into your AMBER tenant before expecting C to hit facts.

### 2) Swap data (your industry / your goals)

```bash
cp -r data/sample_minimal data/my_corp
# edit data/my_corp/corpus/* and data/my_corp/tasks/*.jsonl
export AMBER_DATA_DIR=data/my_corp
python3 scripts/run_bench.py --backend amber
```

Layout and schema: [`data/README.md`](data/README.md).

## Reproduce the published fair_r2 numbers

Shipped `reference/fair_r2/raw/*.jsonl` already contains the 900-row run.
Re-aggregate with **no API key**:

```bash
bash scripts/reproduce.sh
# or:
python3 scripts/summarize.py --data-dir reference/fair_r2
```

To **re-call** the same local_sim protocol (needs your upstream key; ≈900 calls):

```bash
export AMBER_BENCH_BACKEND=local_sim
export UPSTREAM_API_KEY=sk-...    # never commit
python3 scripts/run_bench.py --backend local_sim --data-dir reference/fair_r2
python3 scripts/summarize.py --data-dir reference/fair_r2
```

## Layout

```
scripts/                 # harness only (run / summarize / optional builder)
data/sample_minimal/     # tiny replaceable demo
data/README.md           # how to import your own jsonl
reference/fair_r2/       # published fixture: tasks, contexts, corpus, raw, results
params/                  # default harness params (no secrets)
METHOD.md  ERRATA.md  CHANGELOG-fair-rerun.md
.env.example
```

Python **3.10+ stdlib only** (`requirements.txt` notes this). License: MIT.

## Disclaimer

- Scripts here **assemble requests and score outputs**. They are not the AMBER
  memory implementation.
- Reference fair_r2 numbers were produced with **local_sim → upstream**, not a
  live multi-tenant cloud gateway smoke (see ERRATA). Use `--backend amber`
  against your deployment for product-connected measurements.

# METHOD · AMBER public comparison bench

**method_id (reference fixture):** `amber-public-bench-20261027-r2-fair`  
**Timezone for published run:** Asia/Shanghai

## Role of this repository

This repository is a **public comparison / reproduction harness**.
It is **not** the AMBER memory-layer product source. The harness:

1. Loads a replaceable dataset (`AMBER_DATA_DIR` / `--data-dir`)
2. Calls either **AMBER** (OpenAI-compatible) or an **upstream** chat API
3. Writes `raw/*.jsonl` and aggregates with `scripts/summarize.py`

## Backends

| Backend | Default? | Behavior |
|---------|----------|----------|
| `amber` | **yes** | `C_amber` → `AMBER_BASE_URL` + `AMBER_API_KEY` with memory ON; `A_plain` / `B_fullctx` → upstream (or AMBER memory OFF). Measures a real memory service. |
| `local_sim` | no | Assemble A/B/C messages **locally**, all three arms call upstream. Reproduces `reference/fair_r2` published rows. |

Memory switch (amber backend), documented contract:

- `AMBER_MEMORY=on|off`
- Header `X-AMBER-Memory: on|off` (override names via env)
- Optional dual endpoints `AMBER_BASE_URL_MEMORY_ON` / `_OFF`

## Arms

| Arm | Intent |
|-----|--------|
| A_plain | No memory / no corpus inject |
| B_fullctx | Naive full-corpus (or full-repo window) dump — token upper baseline |
| C_amber | Memory layer ON (real AMBER) **or** local Top-k / narrow window (`local_sim`) |

Primary ratio: `mean(B.prompt_tokens_sum) / mean(C.prompt_tokens_sum)`.

## Reference fixture fairness (r2 vs v1)

Shipped under `reference/fair_r2/`:

1. Daily B ledger = FACT lines only — **no** v1 `NOISE|` / `HIST|` fattening  
2. Prog: B shares ledger facts when gold missing; abstain coaching stripped from C  
3. Protocol `v2_fair` (no bare 「无」 / 「没有」)  
4. Paths resolved from `Path(__file__)` / `--data-dir` — **no** required `/workspace/...`  
5. `build_tasks.py` **refused** unless `FORCE_REBUILD=1` (private sandboxes not shipped)

## Fixed task bank (reference only)

| Track | N | Location |
|-------|--:|----------|
| daily | 50 | `reference/fair_r2/tasks/daily50.jsonl` |
| prog | 30 | `reference/fair_r2/tasks/prog30.jsonl` + `contexts/prog/` |
| lit | 20 | `reference/fair_r2/tasks/lit20.jsonl` + `corpus/lit_*` |

Custom datasets may use fewer rows; keep the same filenames or adjust scripts.

## Literature note

Literature abstracts are **reproduced for evaluation** from public arXiv metadata
(typical non-exclusive distribution for abstracts). This bench does not claim
ownership of the papers. Prefer citing each `arXiv:id`. License of this
**harness + synthetic ledger/tasks** is MIT.

## Run parameters (reference)

- Request model name: `deepseek-chat` (returned name may differ; see raw `model_returned`)
- `temperature=0`, `max_tokens=400`, repeats=3
- Token counts from API `usage` fields

## Reproduce

```bash
# aggregate published raw (no key)
python3 scripts/summarize.py --data-dir reference/fair_r2

# primary: your AMBER
cp .env.example .env   # fill AMBER_* and UPSTREAM_*
python3 scripts/run_bench.py --backend amber --data-dir data/sample_minimal

# optional: re-run local_sim fixture (~900 calls)
python3 scripts/run_bench.py --backend local_sim --data-dir reference/fair_r2
```

Never commit API keys. Public artifacts may include `key_last4` only.

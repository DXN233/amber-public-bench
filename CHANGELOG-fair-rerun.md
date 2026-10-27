# CHANGELOG · fair rerun r2 · harness packaging

## 2026-10-27 · GitHub packaging

- Split **harness** (`scripts/`) vs **reference fixture** (`reference/fair_r2/`)
  vs **replaceable sample** (`data/sample_minimal/`).
- Default backend **`amber`** (OpenAI-compatible `AMBER_BASE_URL` + `AMBER_API_KEY`).
- Keep **`local_sim`** to reproduce published raw numbers.
- Document memory on/off via env / header / dual endpoint (`.env.example`).
- `build_tasks.py` refuses unless `FORCE_REBUILD=1`.
- Clarify in README: this is **not** the memory product source.

## Motivation (fair r2)

Third-party audit P0: v1 daily 236× contained HIST/NOISE fatten; some prog golds
only in C; abstain coaching on C. Re-ran instead of only changing copy.

## v1 → r2 fair

| Item | v1 | r2 fair |
|------|----|---------|
| Daily ledger | FACT + NOISE×80 + HIST×~200 | **FACT only** |
| Daily B÷C prompt | ~236× (invalid as headline) | **9.33×** |
| Prog B gold coverage | partial miss | shared ledger when missing |
| Abstain coaching on C | present | **stripped** |
| Protocol | loose 「无」 | **v2_fair** |
| Raw | old pack | **new measured raw** in `reference/fair_r2/raw/` |

## Files

- Reference fixture: `reference/fair_r2/`
- Sample data: `data/sample_minimal/`
- Harness: `scripts/run_bench.py`, `scripts/summarize.py`

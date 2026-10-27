# AMBER public bench summary

> data_dir=`reference/fair_r2` · method_id=`amber-public-bench-20261027-r2-fair`
> Harness ≠ memory product. Primary path: connect AMBER (`--backend amber`).
> Primary ratio: **B_fullctx ÷ C_amber** prompt_tokens. Scores = protocol_v2_fair; `human_score` empty.

## daily（file expectation up to 50; actual may differ for custom data）

- rows: 450 (ok=450 err=0)
- **C_amber**: prompt Σ mean±std = 7824.0±0.0; completion Σ = 304.7±3.3; completion_rate=0.980±0.000; protocol_score=1.960±0.000
- **B_fullctx**: prompt Σ mean±std = 73036.0±0.0; completion Σ = 363.0±4.2; completion_rate=0.980±0.000; protocol_score=1.960±0.000
- **A_plain**: prompt Σ mean±std = 2086.0±0.0; completion Σ = 118.7±2.4; completion_rate=0.120±0.000; protocol_score=0.240±0.000
- **B/C prompt: 9.33×**; B/C total: 9.03×
- completion_rate lift C−A: +0.860

## prog（file expectation up to 30; actual may differ for custom data）

- rows: 270 (ok=270 err=0)
- **A_plain**: prompt Σ mean±std = 1566.0±0.0; completion Σ = 71.3±7.5; completion_rate=0.167±0.000; protocol_score=0.400±0.000
- **C_amber**: prompt Σ mean±std = 18447.0±0.0; completion Σ = 636.7±21.0; completion_rate=0.700±0.000; protocol_score=1.467±0.000
- **B_fullctx**: prompt Σ mean±std = 280986.0±0.0; completion Σ = 621.3±12.7; completion_rate=0.656±0.016; protocol_score=1.378±0.031
- **B/C prompt: 15.23×**; B/C total: 14.76×
- completion_rate lift C−A: +0.533

## lit（file expectation up to 20; actual may differ for custom data）

- rows: 180 (ok=180 err=0)
- **C_amber**: prompt Σ mean±std = 2129.0±0.0; completion Σ = 278.7±10.4; completion_rate=1.000±0.000; protocol_score=2.000±0.000
- **B_fullctx**: prompt Σ mean±std = 22592.0±0.0; completion Σ = 337.3±3.3; completion_rate=0.900±0.000; protocol_score=1.800±0.000
- **A_plain**: prompt Σ mean±std = 932.0±0.0; completion Σ = 48.3±0.5; completion_rate=0.000±0.000; protocol_score=0.000±0.000
- **B/C prompt: 10.61×**; B/C total: 9.52×
- completion_rate lift C−A: +1.000

## vs v1 reference (if docs/v1_summary_reference.json present)

| track | v1 B÷C | this B÷C | v1 C rate | this C rate | v1 B rate | this B rate |
|---|---:|---:|---:|---:|---:|---:|
| daily | 236.07× | 9.33× | 1.000 | 0.980 | 0.993 | 0.980 |
| prog | 15.04× | 15.23× | 0.744 | 0.700 | 0.611 | 0.656 |
| lit | 10.61× | 10.61× | 1.000 | 1.000 | 0.900 | 0.900 |

See METHOD.md / ERRATA.md. Raw: `raw/*.jsonl`.

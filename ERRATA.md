# ERRATA / honest limits · fair r2 + harness packaging

1. **Harness ≠ product.** This repo does not ship the AMBER memory implementation.
   `--backend amber` talks to **your** OpenAI-compatible AMBER deployment.
2. **Published fair_r2 raw** was produced with **local_sim → upstream DeepSeek**,
   not a multi-tenant cloud-gateway success path (historical gateway reachable but
   401 / no smoke key on the runner). Do not label those rows “cloud AMBER prod”.
3. Request model `deepseek-chat`; raw `model_returned` may be `deepseek-flash`.
4. Retracted marketing number: v1 daily **236×** (HIST/NOISE fatten). Use r2
   **9.33× / 15.23× / 10.61×** only. Comparison table lives in
   `reference/fair_r2/results/summary.md` and `CHANGELOG-fair-rerun.md`.
5. Prog B shared-ledger prepend slightly raises B tokens (15.23× vs v1 15.04×);
   accepted fairness cost.
6. `human_score` remains empty — protocol scores only unless you fill them.
7. `build_tasks.py` is maintainer-only and refused by default.

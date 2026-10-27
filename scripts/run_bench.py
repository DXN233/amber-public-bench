#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AMBER public-bench harness (NOT the memory product itself).

Backends
--------
- amber (default): C arm → AMBER OpenAI-compatible API with memory ON.
  A_plain → upstream (or AMBER memory OFF). B_fullctx → full corpus injected
  client-side to upstream (token/quality baseline). This is the primary path
  for measuring a real memory layer.
- local_sim: assemble A/B/C messages locally; all three arms call UPSTREAM.
  Used to reproduce the published reference/fair_r2 numbers.

Data
----
Replaceable via --data-dir / AMBER_DATA_DIR / AMBER_CORPUS_DIR.
Expected layout under data-dir:
  tasks/{daily50,prog30,lit20}.jsonl
  corpus/{daily_ledger.txt,lit_fullctx.txt}
  contexts/prog/*_{B,C}.txt   (prog only)
  raw/   (outputs written here)
"""
from __future__ import annotations
import argparse, json, os, sys, time, threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

REPO = Path(__file__).resolve().parents[1]

ABSTAIN_CUES = [
    "无法定位", "不存在", "没有该", "无此", "未覆盖", "未找到", "找不到",
    "cannot locate", "not found", "no such", "unknown", "does not exist",
    "没有这个", "并无此", "库内无", "索引无",
]


def load_dotenv(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def resolve_data_dir(cli: str | None) -> Path:
    raw = cli or os.environ.get("AMBER_DATA_DIR") or os.environ.get("AMBER_CORPUS_DIR")
    if not raw:
        raw = "reference/fair_r2"
    p = Path(raw)
    if not p.is_absolute():
        p = (REPO / p).resolve()
    return p


def load_jsonl(path: Path):
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def score_protocol(answer: str, gold: dict) -> tuple[int, bool]:
    ans = (answer or "").casefold()
    abstain = bool(gold.get("abstain") or gold.get("mode") == "abstain")
    if abstain:
        cues = list(ABSTAIN_CUES)
        for m in gold.get("must_any") or []:
            m = str(m)
            if len(m) >= 2 and m not in ("无", "没有", "&", ".py"):
                cues.append(m)
        if any(c.casefold() in ans for c in cues):
            return 2, True
        if any(ch.isdigit() for ch in ans) and len(ans) > 8:
            return 0, False
        return 1, False
    must = [str(m) for m in (gold.get("must_any") or []) if str(m) not in (".py", "&", "无")]
    if not must:
        must = [str(m) for m in (gold.get("must_any") or [])]
    hit = any(m.casefold() in ans for m in must)
    files = gold.get("must_file_any") or []
    fhit = (not files) or any(str(f).casefold() in ans for f in files)
    if hit and fhit:
        return 2, True
    if hit and not fhit:
        return 1, False
    if (not hit) and files and fhit:
        return 1, False
    return 0, False


def chat(endpoint: str, key: str, model: str, messages, temperature: float, max_tokens: int,
         extra_headers: dict | None = None):
    body = json.dumps({
        "model": model, "messages": messages,
        "temperature": temperature, "max_tokens": max_tokens,
    }).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    if extra_headers:
        headers.update(extra_headers)
    req = Request(endpoint, data=body, headers=headers, method="POST")
    t0 = time.time()
    try:
        with urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", "replace")
    except HTTPError as e:
        raw = e.read().decode("utf-8", "replace") if hasattr(e, "read") else str(e)
        return {"error": f"HTTP {e.code}", "latency_ms": int((time.time()-t0)*1000),
                "raw": raw[:500], "prompt_tokens": None, "completion_tokens": None,
                "total_tokens": None, "answer": "", "model_returned": None}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}", "latency_ms": int((time.time()-t0)*1000),
                "raw": "", "prompt_tokens": None, "completion_tokens": None,
                "total_tokens": None, "answer": "", "model_returned": None}
    try:
        d = json.loads(raw)
    except Exception:
        return {"error": "bad_json", "latency_ms": int((time.time()-t0)*1000), "raw": raw[:500],
                "prompt_tokens": None, "completion_tokens": None, "total_tokens": None,
                "answer": "", "model_returned": None}
    usage = d.get("usage") or {}
    ans = ""
    try:
        ans = d["choices"][0]["message"]["content"] or ""
    except Exception:
        ans = ""
    return {"error": None, "latency_ms": int((time.time()-t0)*1000),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "total_tokens": usage.get("total_tokens"),
            "answer": ans, "model_returned": d.get("model"), "raw": ""}


def memory_headers(on: bool) -> dict:
    """Documented AMBER memory switch via header (override with env if needed)."""
    header_name = os.environ.get("AMBER_MEMORY_HEADER", "X-AMBER-Memory")
    val_on = os.environ.get("AMBER_MEMORY_HEADER_ON", "on")
    val_off = os.environ.get("AMBER_MEMORY_HEADER_OFF", "off")
    return {header_name: val_on if on else val_off}


def amber_endpoint(memory_on: bool) -> str:
    """Resolve AMBER chat completions URL. Supports dual-endpoint override."""
    if memory_on:
        base = os.environ.get("AMBER_BASE_URL_MEMORY_ON") or os.environ.get("AMBER_BASE_URL")
    else:
        base = os.environ.get("AMBER_BASE_URL_MEMORY_OFF") or os.environ.get("AMBER_BASE_URL")
    if not base:
        raise RuntimeError("AMBER_BASE_URL not set")
    base = base.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return base + "/chat/completions"


def upstream_endpoint() -> str:
    ep = os.environ.get("UPSTREAM_BASE_URL") or os.environ.get("DEEPSEEK_BASE_URL")
    if ep:
        ep = ep.rstrip("/")
        if ep.endswith("/chat/completions"):
            return ep
        return ep + "/chat/completions"
    return "https://api.deepseek.com/chat/completions"


def build_local_messages(track: str, task: dict, arm: str, ledger: str, lit_full: str,
                         data_dir: Path, system_prompt: str):
    """local_sim / B-arm helper: assemble context client-side."""
    q = task["prompt"]
    if arm == "A_plain":
        user = q
        ctx_chars = 0
    elif arm == "B_fullctx":
        if track == "daily":
            ctx = "\n".join(ln for ln in ledger.splitlines()
                            if ln.strip() and not ln.startswith(("NOISE|", "HIST|")))
        elif track == "lit":
            ctx = lit_full
        else:
            ctx = (data_dir / task["ctx_b"]).read_text(encoding="utf-8", errors="replace")
        user = f"【上下文】\n{ctx}\n\n【问题】\n{q}"
        ctx_chars = len(ctx)
    elif arm == "C_amber":
        if track == "daily":
            lines = [ln for ln in ledger.splitlines()
                     if ln.strip() and not ln.startswith(("NOISE|", "HIST|"))]
            ql = q.casefold()
            scored = []
            for ln in lines:
                toks = [t for t in ln.replace("|", " ").split() if t]
                score = sum(1 for t in toks if t.casefold() in ql)
                for n in (2, 3, 4):
                    for i in range(max(0, len(q) - n + 1)):
                        gram = q[i:i + n]
                        if gram.strip() and gram in ln:
                            score += 1
                scored.append((score, ln))
            scored.sort(key=lambda x: (-x[0], x[1]))
            top = [ln for s, ln in scored[:6] if s > 0] or [ln for s, ln in scored[:3]]
            ctx = "【记忆检索片段】\n" + "\n".join(top)
        elif track == "lit":
            ctx = task.get("amber_snippet") or ""
        else:
            ctx = (data_dir / task["ctx_c"]).read_text(encoding="utf-8", errors="replace")
        user = f"【上下文】\n{ctx}\n\n【问题】\n{q}"
        ctx_chars = len(ctx)
    else:
        raise ValueError(arm)
    return [{"role": "system", "content": system_prompt},
            {"role": "user", "content": user}], ctx_chars


class Runner:
    def __init__(self, data_dir: Path, backend: str, params: dict, workers: int):
        self.data_dir = data_dir
        self.backend = backend
        self.params = params
        self.workers = workers
        self.sys = params.get("system_prompt") or (
            "你是严谨助手。只依据给定上下文回答；上下文未覆盖则答「无法定位」。"
            "不要编造数字或 API。回答尽量短。"
        )
        self.model = os.environ.get("AMBER_MODEL") or os.environ.get("UPSTREAM_MODEL") or params.get("model_requested") or "deepseek-chat"
        self.temp = float(params.get("temperature", 0))
        self.maxtok = int(params.get("max_tokens", 400))
        self.raw_dir = data_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = data_dir / "RUNLOG.md"
        self.lock = threading.Lock()
        self.ledger = ""
        self.lit_full = ""
        lp = data_dir / "corpus" / "daily_ledger.txt"
        if lp.exists():
            self.ledger = lp.read_text(encoding="utf-8")
        lf = data_dir / "corpus" / "lit_fullctx.txt"
        if lf.exists():
            self.lit_full = lf.read_text(encoding="utf-8")
        self.amber_key = os.environ.get("AMBER_API_KEY", "")
        self.upstream_key = (os.environ.get("UPSTREAM_API_KEY")
                             or os.environ.get("DEEPSEEK_API_KEY") or "")
        self.amber_key4 = self.amber_key[-4:] if self.amber_key else "none"
        self.up_key4 = self.upstream_key[-4:] if self.upstream_key else "none"

    def log(self, msg: str):
        line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
        print(line, flush=True)
        with self.lock:
            if not self.log_path.exists():
                self.log_path.write_text(
                    f"# RUNLOG\n\nstarted {time.strftime('%Y-%m-%d %H:%M:%S %Z')}\n"
                    f"backend={self.backend} data_dir={self.data_dir}\n\n",
                    encoding="utf-8")
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")

    def existing_keys(self, path: Path) -> set:
        done = set()
        if not path.exists():
            return done
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            done.add((r["task_id"], r["arm"], r["run_i"]))
        return done

    def append_row(self, path: Path, row: dict):
        with self.lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def dispatch(self, track: str, task: dict, arm: str):
        """Return (result_dict, ctx_chars, endpoint_label, key_last4)."""
        if self.backend == "local_sim":
            if not self.upstream_key:
                raise RuntimeError("local_sim requires UPSTREAM_API_KEY or DEEPSEEK_API_KEY")
            messages, ctx_chars = build_local_messages(
                track, task, arm, self.ledger, self.lit_full, self.data_dir, self.sys)
            ep = upstream_endpoint()
            res = chat(ep, self.upstream_key, self.model, messages, self.temp, self.maxtok)
            return res, ctx_chars, "upstream", self.up_key4

        # backend == amber (primary)
        if arm == "C_amber":
            if not self.amber_key:
                raise RuntimeError("amber backend C arm requires AMBER_API_KEY")
            # Real memory layer: send question only; AMBER retrieves.
            # Optional: pass a hint query in a vendor header for debugging.
            messages = [
                {"role": "system", "content": self.sys},
                {"role": "user", "content": task["prompt"]},
            ]
            hdrs = memory_headers(True)
            # allow env AMBER_MEMORY=on|off to force
            mem_env = os.environ.get("AMBER_MEMORY", "on").lower()
            if mem_env in ("0", "off", "false", "no"):
                hdrs = memory_headers(False)
            ep = amber_endpoint(memory_on=True)
            model = os.environ.get("AMBER_MODEL") or self.model
            res = chat(ep, self.amber_key, model, messages, self.temp, self.maxtok, hdrs)
            return res, 0, "amber_memory_on", self.amber_key4

        if arm == "A_plain":
            # Prefer upstream plain; fall back to AMBER memory OFF.
            messages = [
                {"role": "system", "content": self.sys},
                {"role": "user", "content": task["prompt"]},
            ]
            if self.upstream_key:
                ep = upstream_endpoint()
                res = chat(ep, self.upstream_key, self.model, messages, self.temp, self.maxtok)
                return res, 0, "upstream", self.up_key4
            if not self.amber_key:
                raise RuntimeError("A_plain needs UPSTREAM_API_KEY/DEEPSEEK_API_KEY or AMBER_API_KEY")
            ep = amber_endpoint(memory_on=False)
            res = chat(ep, self.amber_key, os.environ.get("AMBER_MODEL") or self.model,
                       messages, self.temp, self.maxtok, memory_headers(False))
            return res, 0, "amber_memory_off", self.amber_key4

        if arm == "B_fullctx":
            # Full-context baseline (client-side inject) — not the memory product.
            messages, ctx_chars = build_local_messages(
                track, task, "B_fullctx", self.ledger, self.lit_full, self.data_dir, self.sys)
            if self.upstream_key:
                ep = upstream_endpoint()
                res = chat(ep, self.upstream_key, self.model, messages, self.temp, self.maxtok)
                return res, ctx_chars, "upstream_fullctx", self.up_key4
            if not self.amber_key:
                raise RuntimeError("B_fullctx needs UPSTREAM_API_KEY/DEEPSEEK_API_KEY or AMBER_API_KEY")
            ep = amber_endpoint(memory_on=False)
            res = chat(ep, self.amber_key, os.environ.get("AMBER_MODEL") or self.model,
                       messages, self.temp, self.maxtok, memory_headers(False))
            return res, ctx_chars, "amber_fullctx_memory_off", self.amber_key4

        raise ValueError(arm)

    def run_one(self, track, task, arm, run_i, path):
        result = None
        ctx_chars = 0
        ep_label = ""
        key4 = "none"
        err_pre = None
        for attempt in range(3):
            try:
                result, ctx_chars, ep_label, key4 = self.dispatch(track, task, arm)
            except Exception as e:
                err_pre = f"{type(e).__name__}: {e}"
                result = {"error": err_pre, "latency_ms": 0, "prompt_tokens": None,
                          "completion_tokens": None, "total_tokens": None,
                          "answer": "", "model_returned": None, "raw": ""}
                break
            if not result["error"]:
                break
            time.sleep(1.5 * (attempt + 1))
        gold = task.get("gold") or {}
        ps, passed = score_protocol(result.get("answer") or "", gold)
        row = {
            "track": track, "task_id": task["id"], "arm": arm, "run_i": run_i,
            "backend": self.backend, "endpoint_label": ep_label,
            "model_requested": self.model, "model_returned": result.get("model_returned"),
            "temperature": self.temp, "max_tokens": self.maxtok,
            "latency_ms": result.get("latency_ms"),
            "prompt_tokens": result.get("prompt_tokens"),
            "completion_tokens": result.get("completion_tokens"),
            "total_tokens": result.get("total_tokens"),
            "ctx_chars": ctx_chars,
            "answer": (result.get("answer") or "")[:2000],
            "protocol_score": ps if not result.get("error") else None,
            "human_score": None,
            "pass": passed if not result.get("error") else False,
            "gold": gold, "error": result.get("error"),
            "key_last4": key4,
            "notes": (result.get("raw") or "")[:300] if result.get("error") else "",
            "category": task.get("category"),
            "source": task.get("source") or task.get("doi_or_arxiv"),
            "source_sha": task.get("source_sha"),
            "rubric": "protocol_v2_fair",
            "method_id": self.params.get("method_id"),
            "data_dir": str(self.data_dir.relative_to(REPO)) if str(self.data_dir).startswith(str(REPO)) else str(self.data_dir),
        }
        self.append_row(path, row)
        return row

    def run_track(self, track: str, arms: list, repeats: int, limit: int):
        filemap = {"daily": "daily50.jsonl", "prog": "prog30.jsonl", "lit": "lit20.jsonl"}
        tpath = self.data_dir / "tasks" / filemap[track]
        tasks = load_jsonl(tpath)
        if not tasks:
            self.log(f"{track}: SKIP no tasks at {tpath}")
            return
        if limit:
            tasks = tasks[:limit]
        path = self.raw_dir / f"{track}.jsonl"
        done = self.existing_keys(path)
        jobs = []
        for task in tasks:
            for arm in arms:
                for run_i in range(1, repeats + 1):
                    if (task["id"], arm, run_i) in done:
                        continue
                    jobs.append((task, arm, run_i))
        self.log(f"{track}: tasks={len(tasks)} pending_calls={len(jobs)} (resume_skip={len(done)})")
        if not jobs:
            return
        ok = err = 0
        with ThreadPoolExecutor(max_workers=self.workers) as ex:
            futs = [ex.submit(self.run_one, track, task, arm, run_i, path)
                    for task, arm, run_i in jobs]
            for i, fut in enumerate(as_completed(futs), 1):
                row = fut.result()
                if row.get("error"):
                    err += 1
                else:
                    ok += 1
                if i % 25 == 0 or i == len(futs):
                    self.log(f"{track}: progress {i}/{len(futs)} ok={ok} err={err}")
        self.log(f"{track}: done ok={ok} err={err}")


def main():
    load_dotenv(REPO / ".env")
    ap = argparse.ArgumentParser(description="AMBER public-bench harness")
    ap.add_argument("--backend", choices=["amber", "local_sim"],
                    default=os.environ.get("AMBER_BENCH_BACKEND", "amber"),
                    help="amber=hit AMBER memory layer (default); local_sim=reproduce published fixture")
    ap.add_argument("--data-dir", default=None,
                    help="Dataset root (tasks/corpus/contexts). Default: AMBER_DATA_DIR or reference/fair_r2")
    ap.add_argument("--tracks", default="daily,prog,lit")
    ap.add_argument("--arms", default="A_plain,B_fullctx,C_amber")
    ap.add_argument("--repeats", type=int, default=0, help="0 = use params/repeats")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    data_dir = resolve_data_dir(args.data_dir)
    # params: data-dir params override repo params
    params = {}
    for cand in [REPO / "params" / "run_params.json", data_dir / "params" / "run_params.json"]:
        if cand.exists():
            params.update(json.loads(cand.read_text(encoding="utf-8")))
    repeats = args.repeats or int(params.get("repeats") or 3)
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    tracks = [t.strip() for t in args.tracks.split(",") if t.strip()]

    if args.backend == "amber" and not os.environ.get("AMBER_API_KEY"):
        print("BLOCKED: amber backend needs AMBER_API_KEY (and AMBER_BASE_URL).", file=sys.stderr)
        print("  Or use --backend local_sim with UPSTREAM_API_KEY/DEEPSEEK_API_KEY to reproduce reference.", file=sys.stderr)
        print("  See .env.example and README.md.", file=sys.stderr)
        sys.exit(2)
    if args.backend == "local_sim" and not (os.environ.get("UPSTREAM_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")):
        print("BLOCKED: local_sim needs UPSTREAM_API_KEY or DEEPSEEK_API_KEY.", file=sys.stderr)
        sys.exit(2)

    runner = Runner(data_dir, args.backend, params, args.workers)
    runner.log(f"start backend={args.backend} data_dir={data_dir} repeats={repeats} arms={arms}")
    for track in tracks:
        runner.run_track(track, arms, repeats, args.limit)
    runner.log("all tracks finished")


if __name__ == "__main__":
    main()

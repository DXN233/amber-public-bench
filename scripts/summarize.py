#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aggregate raw/*.jsonl → results/summary.{md,json}. Stdlib only. No API calls."""
from __future__ import annotations
import argparse, json, os, statistics, sys
from pathlib import Path
from collections import defaultdict

REPO = Path(__file__).resolve().parents[1]


def resolve_data_dir(cli: str | None) -> Path:
    raw = cli or os.environ.get("AMBER_DATA_DIR") or os.environ.get("AMBER_CORPUS_DIR") or "reference/fair_r2"
    p = Path(raw)
    if not p.is_absolute():
        p = (REPO / p).resolve()
    return p


def load(raw_dir: Path, track: str):
    p = raw_dir / f"{track}.jsonl"
    if not p.exists():
        return []
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def mean_std(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return None, None
    if len(xs) == 1:
        return xs[0], 0.0
    return statistics.mean(xs), statistics.pstdev(xs)


def agg_track(track, rows):
    by_arm_run = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r.get("error"):
            continue
        by_arm_run[r["arm"]][r["run_i"]].append(r)
    out = {"track": track, "n_rows": len(rows),
           "n_ok_rows": sum(1 for r in rows if not r.get("error")),
           "n_err_rows": sum(1 for r in rows if r.get("error")), "arms": {}}
    for arm, runs in by_arm_run.items():
        run_stats = []
        for run_i, rs in sorted(runs.items()):
            pt = sum(r["prompt_tokens"] or 0 for r in rs)
            ct = sum(r["completion_tokens"] or 0 for r in rs)
            tt = sum(r["total_tokens"] or 0 for r in rs)
            n = len(rs)
            completed = sum(1 for r in rs if r.get("protocol_score") == 2)
            scores = [r["protocol_score"] for r in rs if r.get("protocol_score") is not None]
            run_stats.append({
                "run_i": run_i, "n": n,
                "prompt_tokens_sum": pt, "completion_tokens_sum": ct, "total_tokens_sum": tt,
                "completion_rate": completed / n if n else None,
                "protocol_score_mean": statistics.mean(scores) if scores else None,
            })
        def collect(key):
            return [x[key] for x in run_stats if x[key] is not None]
        pm, ps = mean_std(collect("prompt_tokens_sum"))
        tm, ts = mean_std(collect("total_tokens_sum"))
        cm, cs = mean_std(collect("completion_tokens_sum"))
        crm, crs = mean_std(collect("completion_rate"))
        sm, ss = mean_std(collect("protocol_score_mean"))
        out["arms"][arm] = {
            "runs": run_stats,
            "prompt_tokens_sum_mean": pm, "prompt_tokens_sum_std": ps,
            "completion_tokens_sum_mean": cm, "completion_tokens_sum_std": cs,
            "total_tokens_sum_mean": tm, "total_tokens_sum_std": ts,
            "completion_rate_mean": crm, "completion_rate_std": crs,
            "protocol_score_mean": sm, "protocol_score_std": ss,
            "n_tasks_per_run": run_stats[0]["n"] if run_stats else 0,
        }
    arms = out["arms"]
    ratios = {}
    if "B_fullctx" in arms and "C_amber" in arms:
        b = arms["B_fullctx"]["prompt_tokens_sum_mean"]
        c = arms["C_amber"]["prompt_tokens_sum_mean"]
        ratios["B_over_C_prompt"] = (b / c) if (b and c) else None
        bt = arms["B_fullctx"]["total_tokens_sum_mean"]
        ct = arms["C_amber"]["total_tokens_sum_mean"]
        ratios["B_over_C_total"] = (bt / ct) if (bt and ct) else None
    if "A_plain" in arms and "C_amber" in arms:
        ratios["C_minus_A_completion_rate"] = None
        if (arms["C_amber"]["completion_rate_mean"] is not None
                and arms["A_plain"]["completion_rate_mean"] is not None):
            ratios["C_minus_A_completion_rate"] = (
                arms["C_amber"]["completion_rate_mean"] - arms["A_plain"]["completion_rate_mean"])
    out["ratios"] = ratios
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default=None)
    args = ap.parse_args()
    data_dir = resolve_data_dir(args.data_dir)
    raw_dir = data_dir / "raw"
    res_dir = data_dir / "results"
    res_dir.mkdir(parents=True, exist_ok=True)

    v1 = {}
    v1p = data_dir / "docs" / "v1_summary_reference.json"
    if v1p.exists():
        try:
            v1 = json.loads(v1p.read_text(encoding="utf-8"))
        except Exception:
            v1 = {}

    method_id = "unknown"
    rp = data_dir / "params" / "run_params.json"
    if rp.exists():
        try:
            method_id = json.loads(rp.read_text(encoding="utf-8")).get("method_id") or method_id
        except Exception:
            pass

    summary = {
        "method_id": method_id,
        "data_dir": str(data_dir.relative_to(REPO)) if str(data_dir).startswith(str(REPO)) else str(data_dir),
        "harness_note": "This repo is a public comparison harness, not the AMBER memory product source.",
        "tracks": {},
        "notes": [
            "主倍数 = B_fullctx.prompt_tokens_sum / C_amber.prompt_tokens_sum（三轮 mean）",
            "主表分数 = protocol_score（v2_fair）；human_score 待填",
            "reference/fair_r2 raw = local_sim 直连 upstream 的已发表对照；接 AMBER 实测请 --backend amber 另写 raw",
        ],
    }
    md = [
        f"# AMBER public bench summary",
        "",
        f"> data_dir=`{summary['data_dir']}` · method_id=`{method_id}`",
        "> Harness ≠ memory product. Primary path: connect AMBER (`--backend amber`).",
        "> Primary ratio: **B_fullctx ÷ C_amber** prompt_tokens. Scores = protocol_v2_fair; `human_score` empty.",
        "",
    ]
    compare_rows = []
    for track, n_expect in [("daily", 50), ("prog", 30), ("lit", 20)]:
        rows = load(raw_dir, track)
        agg = agg_track(track, rows)
        summary["tracks"][track] = agg
        md.append(f"## {track}（file expectation up to {n_expect}; actual may differ for custom data）")
        md.append("")
        if not rows:
            md.append("_no data_"); md.append(""); continue
        md.append(f"- rows: {agg['n_rows']} (ok={agg['n_ok_rows']} err={agg['n_err_rows']})")
        for arm, st in agg["arms"].items():
            md.append(
                f"- **{arm}**: prompt Σ mean±std = "
                f"{st['prompt_tokens_sum_mean']:.1f}±{st['prompt_tokens_sum_std']:.1f}; "
                f"completion Σ = {st['completion_tokens_sum_mean']:.1f}±{st['completion_tokens_sum_std']:.1f}; "
                f"completion_rate={st['completion_rate_mean']:.3f}±{st['completion_rate_std']:.3f}; "
                f"protocol_score={st['protocol_score_mean']:.3f}±{st['protocol_score_std']:.3f}"
            )
        r = agg.get("ratios") or {}
        if r.get("B_over_C_prompt") is not None:
            md.append(f"- **B/C prompt: {r['B_over_C_prompt']:.2f}×**; B/C total: {r.get('B_over_C_total'):.2f}×")
            v1r = None
            try:
                v1r = (((v1.get("tracks") or {}).get(track) or {}).get("ratios") or {}).get("B_over_C_prompt")
            except Exception:
                v1r = None
            compare_rows.append((
                track, v1r, r["B_over_C_prompt"],
                (((v1.get("tracks") or {}).get(track) or {}).get("arms") or {}).get("C_amber", {}).get("completion_rate_mean"),
                agg["arms"].get("C_amber", {}).get("completion_rate_mean"),
                (((v1.get("tracks") or {}).get(track) or {}).get("arms") or {}).get("B_fullctx", {}).get("completion_rate_mean"),
                agg["arms"].get("B_fullctx", {}).get("completion_rate_mean"),
            ))
        if r.get("C_minus_A_completion_rate") is not None:
            md.append(f"- completion_rate lift C−A: {r['C_minus_A_completion_rate']:+.3f}")
        md.append("")

    if compare_rows and any(a is not None for _, a, *_ in compare_rows):
        md.append("## vs v1 reference (if docs/v1_summary_reference.json present)")
        md.append("")
        md.append("| track | v1 B÷C | this B÷C | v1 C rate | this C rate | v1 B rate | this B rate |")
        md.append("|---|---:|---:|---:|---:|---:|---:|")
        for track, v1r, r2r, v1c, r2c, v1b, r2b in compare_rows:
            def fr(x):
                return "—" if x is None else f"{x:.2f}×"
            def ft(x):
                return "—" if x is None else f"{x:.3f}"
            md.append(f"| {track} | {fr(v1r)} | {fr(r2r)} | {ft(v1c)} | {ft(r2c)} | {ft(v1b)} | {ft(r2b)} |")
        md.append("")

    md.append("See METHOD.md / ERRATA.md. Raw: `raw/*.jsonl`.")
    summary["compare_v1"] = [
        {"track": t, "v1_B_over_C": a, "this_B_over_C": b,
         "v1_C_rate": c, "this_C_rate": d, "v1_B_rate": e, "this_B_rate": f}
        for t, a, b, c, d, e, f in compare_rows
    ]
    (res_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (res_dir / "summary.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()

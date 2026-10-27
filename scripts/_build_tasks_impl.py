#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import json, shutil, re, os, sys
from pathlib import Path

ROOT = Path(os.environ.get("AMBER_BUILD_OUT") or Path(__file__).resolve().parents[1])
TASKS = ROOT / "tasks"
CTX = ROOT / "contexts" / "prog"
CORPUS = ROOT / "corpus"
PARAMS = ROOT / "params"
for d in (TASKS, CTX, CORPUS, PARAMS):
    d.mkdir(parents=True, exist_ok=True)

# Upstream sandboxes (build-time only; package ships prebuilt contexts)
# Maintainer sandboxes (NOT shipped). Override via env if you must rebuild.
GAB = Path(os.environ.get("AMBER_SB_GAB", "") or "/nonexistent/gab")
TCTX = Path(os.environ.get("AMBER_SB_TCTX", "") or "/nonexistent/tctx")
GAP1 = Path(os.environ.get("AMBER_SB_GAP1", "") or "/nonexistent/gap1")
GAP2 = Path(os.environ.get("AMBER_SB_GAP2", "") or "/nonexistent/gap2")
GAP2B = Path(os.environ.get("AMBER_SB_GAP2B", "") or "/nonexistent/gap2b")


def wjsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


# ---------- Daily: FACT only (no NOISE/HIST) ----------
LEDGER_LINES = [
    "FACT|price_db_count|价格库一共入库 145 条|enterprise|2026-09-01",
    "FACT|plus_monthly|Plus会员月费 ¥29|billing|2026-08-12",
    "FACT|jiangwan_recon|江湾对账成功率 95.5%（107/112）|ops|2026-09-18",
    "FACT|tea_north_star|茶企北极星指标：流水同比|product|2026-07-03",
    "FACT|office_city|办公城市：深圳南山|profile|2026-06-01",
    "FACT|pref_lang|用户偏好：技术答复用简体中文，代码注释英文|pref|2026-06-02",
    "FACT|pref_tone|用户偏好：拒绝对未覆盖事实瞎猜，应答「无法定位」|pref|2026-06-02",
    "FACT|tz|时区约定：Asia/Shanghai (UTC+8)|pref|2026-06-01",
    "FACT|deploy_host|公测网关主机名 shenzhenbeichenhuizhi.site|ops|2026-10-17",
    "FACT|tenant_smoke|测试租户 id=smoke-grok-20261025（key 仅末4公开）|ops|2026-10-25",
    "FACT|window_span_verify|开工约定 WINDOW_SPAN_VERIFY=1600|eng|2026-10-20",
    "FACT|window_fallback|开工约定 WINDOW_FALLBACK_HEAD=800|eng|2026-10-20",
    "FACT|honest_mark|HONEST_EXIT_MARK=无法定位|eng|2026-10-20",
    "FACT|resident_max|RESIDENT_MAX_CHARS=4000|eng|2026-10-20",
    "FACT|meeting_weekday|周会固定周二 10:00 Asia/Shanghai|calendar|2026-05-10",
    "FACT|budget_daily|日预算软上限：上游 completion 不计入营销口径；对照看 prompt|billing|2026-10-01",
    "FACT|repo_policy|编程默认：账本优先于源码种植错误值|eng|2026-10-21",
    "FACT|contact_alias|对外署名：Micheng Shen（论文）；产品称呼纳西妲|profile|2026-10-24",
    "FACT|ci_runner|CI 默认 runner 标签：linux-x64-selfhost|eng|2026-09-09",
    "FACT|db_primary|主库别名 amber_ledger_v3|eng|2026-08-28",
    "FACT|sla_p95|点查 P95 目标 < 800ms（本地）|ops|2026-09-01",
    "FACT|model_default|默认上游模型请求名 deepseek-chat|ops|2026-10-01",
    "FACT|gap_flag|AMBER_GAP_V1_V2 默认开启；关=0|ops|2026-10-26",
    "FACT|tea_sku_count|茶企 SKU 在册 38 个|product|2026-07-04",
    "FACT|recon_owner|对账负责人花名：青禾|ops|2026-09-18",
    "FACT|pref_no_emoji|用户偏好：正式报告不要 emoji|pref|2026-06-03",
    "FACT|ship_addr_city|收货城市：上海|profile|2026-04-02",
    "FACT|vpn_profile|办公 VPN 配置名 amber-office-a|ops|2026-05-20",
    "FACT|backup_cron|账本备份 cron：每天 03:15 Asia/Shanghai|ops|2026-06-15",
    "FACT|alert_channel|告警频道：#amber-ops|ops|2026-06-16",
    "FACT|lint_rule|LEDGER 索引值行 append-only，禁止改写|eng|2026-10-20",
    "FACT|test_cmd|本机验收命令：pytest -q harness|eng|2026-10-22",
    "FACT|color_theme|青青桌面主题色约定：竹青 #2F6F4E|product|2026-10-26",
    "FACT|nap_default|小憩默认 25 分钟|product|2026-10-26",
    "FACT|focus_block|专注块默认 50 分钟|product|2026-10-26",
    "FACT|privacy_bucket|私密桶前缀 private/ 不进 Today 聚合|product|2026-10-26",
    "FACT|review_gate|待审确认门：外发前必须 human_confirm=true|product|2026-10-26",
    "FACT|arxiv_alias|arXiv 显示名 Micheng Shen / nahida123|profile|2026-10-24",
    "FACT|max_tokens_bench|公开对照 max_tokens=400 temperature=0|eng|2026-10-27",
    "FACT|plain_arm|对照臂 A_plain=无记忆注入|eng|2026-10-27",
    "FACT|full_arm|对照臂 B_fullctx=全文账本/全文仓|eng|2026-10-27",
    "FACT|amber_arm|对照臂 C_amber=检索注入/窄窗|eng|2026-10-27",
    "FACT|sku_top|茶企爆款 SKU：龙井礼盒-A|product|2026-07-05",
    "FACT|error_budget|月错误预算 0.5%|ops|2026-08-01",
    "FACT|oncall|本周 oncall：青禾|ops|2026-10-20",
    "FACT|doc_root|内部文档根：docs/USAGE-TRACKS.md|eng|2026-09-15",
    "FACT|sample_passphrase_hint|示例口令提示词仅存 vault，不进账本正文|security|2026-10-01",
    "FACT|forbidden_guess|禁止对未入库价格/成功率做数值猜测|pref|2026-06-02",
    "FACT|lit_judge|科研判据：优先引用 DOI/arXiv id|research|2026-09-20",
    "FACT|mem_cap|常驻层注入上限 4000 字符|eng|2026-10-20",
]
assert not any(l.startswith(("NOISE|", "HIST|")) for l in LEDGER_LINES)
(CORPUS / "daily_ledger.txt").write_text("\n".join(LEDGER_LINES) + "\n", encoding="utf-8")
FULL_LEDGER = "\n".join(LEDGER_LINES)

daily_specs = [
    ("D01", "fact", "价格库一共入库多少条？", ["145"], False),
    ("D02", "fact", "Plus会员月费是多少？", ["29"], False),
    ("D03", "fact", "江湾对账成功率是多少？", ["95.5", "107/112"], False),
    ("D04", "fact", "茶企北极星指标是什么？", ["流水", "同比"], False),
    ("D05", "fact", "办公城市在哪？", ["深圳", "南山"], False),
    ("D06", "pref", "技术答复应用什么语言？", ["简体中文"], False),
    ("D07", "pref", "对未覆盖事实应如何处理？", ["无法定位"], False),
    ("D08", "fact", "时区约定是什么？", ["Asia/Shanghai", "UTC+8", "上海"], False),
    ("D09", "fact", "公测网关主机名？", ["shenzhenbeichenhuizhi.site"], False),
    ("D10", "fact", "测试租户 id 是什么？", ["smoke-grok-20261025"], False),
    ("D11", "convention", "WINDOW_SPAN_VERIFY 约定值？", ["1600"], False),
    ("D12", "convention", "WINDOW_FALLBACK_HEAD 约定值？", ["800"], False),
    ("D13", "convention", "诚实出口标记文案？", ["无法定位"], False),
    ("D14", "convention", "RESIDENT_MAX_CHARS 是多少？", ["4000"], False),
    ("D15", "fact", "周会定在周几几点？", ["周二", "10:00"], False),
    ("D16", "convention", "编程时账本与源码种植冲突听谁的？", ["账本"], False),
    ("D17", "fact", "论文对外署名？", ["Micheng Shen"], False),
    ("D18", "fact", "CI runner 标签？", ["linux-x64-selfhost"], False),
    ("D19", "fact", "主库别名？", ["amber_ledger_v3"], False),
    ("D20", "fact", "点查 P95 目标？", ["800ms", "800"], False),
    ("D21", "fact", "默认上游模型请求名？", ["deepseek-chat"], False),
    ("D22", "fact", "如何关闭 gap-v1-v2？", ["AMBER_GAP_V1_V2=0", "=0"], False),
    ("D23", "fact", "茶企 SKU 在册多少个？", ["38"], False),
    ("D24", "fact", "对账负责人花名？", ["青禾"], False),
    ("D25", "pref", "正式报告能否用 emoji？", ["不要", "不要 emoji", "无 emoji"], False),
    ("D26", "fact", "收货城市？", ["上海"], False),
    ("D27", "fact", "办公 VPN 配置名？", ["amber-office-a"], False),
    ("D28", "fact", "账本备份 cron？", ["03:15"], False),
    ("D29", "fact", "告警频道？", ["#amber-ops", "amber-ops"], False),
    ("D30", "convention", "LEDGER 索引值行可否改写？", ["append-only", "禁止改写", "禁止"], False),
    ("D31", "fact", "本机验收命令？", ["pytest"], False),
    ("D32", "fact", "青青桌面主题色约定？", ["#2F6F4E", "竹青"], False),
    ("D33", "fact", "小憩默认多久？", ["25"], False),
    ("D34", "fact", "专注块默认多久？", ["50"], False),
    ("D35", "convention", "私密桶前缀是什么？是否进 Today？", ["private/", "不进"], False),
    ("D36", "convention", "外发前待审确认字段？", ["human_confirm"], False),
    ("D37", "fact", "arXiv 显示名？", ["Micheng Shen"], False),
    ("D38", "fact", "公开对照 max_tokens？", ["400"], False),
    ("D39", "fact", "对照臂 A_plain 定义？", ["无记忆"], False),
    ("D40", "fact", "茶企爆款 SKU？", ["龙井礼盒-A", "龙井"], False),
    ("D41", "fact", "月错误预算？", ["0.5%"], False),
    ("D42", "fact", "本周 oncall？", ["青禾"], False),
    ("D43", "fact", "内部文档根文件？", ["USAGE-TRACKS"], False),
    ("D44", "fact", "常驻层注入上限字符数？", ["4000"], False),
    ("D45", "abstain", "欧洲仓对账成功率是多少？", ["无法定位"], True),
    ("D46", "abstain", "Plus 年费是多少？（账本仅有月费）", ["无法定位"], True),
    ("D47", "abstain", "用户的银行卡号后四位？", ["无法定位"], True),
    ("D48", "abstain", "未入库的「星巴克联名茶」单价？", ["无法定位"], True),
    ("D49", "pref", "代码注释应用什么语言？", ["英文"], False),
    ("D50", "fact", "产品侧对用户的称呼？", ["纳西妲"], False),
]
daily = []
for tid, cat, prompt, golds, abstain in daily_specs:
    daily.append({
        "id": tid, "track": "daily", "category": cat, "prompt": prompt,
        "gold": {"must_any": golds, "abstain": abstain},
        "rubric": "protocol_v2_fair", "retrieval_query": prompt,
    })
wjsonl(TASKS / "daily50.jsonl", daily)

# ---------- Literature (unchanged content) ----------
PAPERS = [
    ("2404.11018", "Leave No Context Behind: Efficient Infinite Context Transformers with Infini-attention",
     "We introduce Infini-attention, which incorporates compressive memory into attention to enable Transformer LLMs to effectively model infinitely long contexts with bounded memory and computation. Experiments show strong performance on long-context language modeling and passkey retrieval."),
    ("2307.03172", "Lost in the Middle: How Language Models Use Long Contexts",
     "We analyze how language models use long contexts and find that performance is often highest when relevant information occurs at the beginning or end of the input context, and significantly degrades when models must access relevant information in the middle."),
    ("2410.10813", "LongMemEval: Benchmarking Chat Assistants on Long-Term Interactive Memory",
     "We introduce LongMemEval, a comprehensive benchmark for evaluating long-term memory in chat assistants, covering information extraction, multi-session reasoning, knowledge updates, temporal reasoning, and abstention."),
    ("2210.03629", "ReAct: Synergizing Reasoning and Acting in Language Models",
     "We introduce ReAct, a paradigm that combines reasoning traces and task-specific actions in an interleaved manner, enabling LLMs to induce better representations and interact with external environments."),
    ("2310.06117", "MemGPT: Towards LLMs as Operating Systems",
     "We propose MemGPT, a system that virtualizes LLM context windows using hierarchical memory management inspired by operating systems, enabling extended conversations and document analysis beyond the LLM context limit."),
    ("2402.09727", "RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval",
     "RAPTOR constructs a recursive tree of summaries for retrieval-augmented generation, allowing models to use information at different levels of abstraction across long documents."),
    ("2312.10997", "Retrieval-Augmented Generation for Large Language Models: A Survey",
     "A survey of RAG methods covering naive RAG, advanced RAG, and modular RAG, discussing retrieval quality, augmentation strategies, and evaluation challenges."),
    ("2005.11401", "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
     "RAG combines a pre-trained parametric memory with a non-parametric dense vector index of Wikipedia, improving performance on knowledge-intensive NLP tasks."),
    ("2305.14251", "Toolformer: Language Models Can Teach Themselves to Use Tools",
     "Toolformer is an LLM trained to decide which APIs to call, when to call them, what arguments to pass, and how to incorporate results into future token prediction."),
    ("2212.10560", "Self-Instruct: Aligning Language Models with Self-Generated Instructions",
     "Self-Instruct improves instruction following by bootstrapping off the model's own generations, constructing a large instruction dataset with minimal human labeling."),
    ("2305.18290", "Let's Verify Step by Step",
     "Process-based reward models that provide feedback for each reasoning step outperform outcome-based reward models on mathematical reasoning benchmarks."),
    ("2201.11903", "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models",
     "Chain-of-thought prompting elicits multi-step reasoning by providing intermediate reasoning steps in few-shot exemplars, improving performance on arithmetic and symbolic reasoning."),
    ("2305.10601", "Tree of Thoughts: Deliberate Problem Solving with Large Language Models",
     "Tree of Thoughts generalizes chain-of-thought by exploring multiple reasoning paths as a tree, with deliberate decision-making via search algorithms."),
    ("2401.04398", "Agent Laboratory: Using LLM Agents as Research Assistants",
     "Agent Laboratory is a framework where LLM agents collaborate to conduct research, including literature review, experimentation, and report writing."),
    ("2310.08560", "FireAct: Toward Language Agent Fine-tuning",
     "FireAct studies fine-tuning language agents with diverse trajectories and shows that fine-tuning can improve agent robustness and efficiency compared to prompting alone."),
    ("2406.04692", "A Survey on Retrieval-Augmented Text Generation for Large Language Models",
     "This survey reviews retrieval-augmented text generation architectures, training strategies, and applications for large language models."),
    ("2308.09583", "The Rise and Potential of Large Language Model Based Agents: A Survey",
     "A survey of LLM-based agents covering perception, planning, memory, and tool use, and discussing open challenges for autonomous agents."),
    ("2402.01622", "An Empirical Study of Retrieval-Augmented Code Generation",
     "Empirical study showing how retrieval of similar code snippets improves code generation quality across models and languages."),
    ("2501.00663", "KV-Cache Compression Methods for Efficient Long-Context Inference: A Survey",
     "A survey of key-value cache compression techniques that reduce memory and latency for long-context LLM inference while preserving quality."),
    ("2309.00267", "Cognitive Architectures for Language Agents",
     "CoALA proposes a conceptual framework for language agents that organizes memory, action spaces, and decision-making inspired by cognitive science."),
]
(CORPUS / "lit_papers.json").write_text(json.dumps([
    {"arxiv_id": a, "title": t, "abstract": ab} for a, t, ab in PAPERS
], ensure_ascii=False, indent=2), encoding="utf-8")
FULL_LIT = "\n\n".join([f"arXiv:{a}\nTitle:{t}\nAbstract:{ab}" for a, t, ab in PAPERS])
(CORPUS / "lit_fullctx.txt").write_text(FULL_LIT, encoding="utf-8")

lit_qs = [
    ("L01", "2404.11018", "Infini-attention 把什么引入注意力以支持无限上下文？", ["compressive memory", "压缩记忆", "Infini-attention"]),
    ("L02", "2307.03172", "Lost in the Middle 发现相关信息在上下文什么位置时性能常最好？", ["beginning", "end", "开头", "结尾", "两端"]),
    ("L03", "2410.10813", "LongMemEval 主要评测什么能力？", ["long-term memory", "长期记忆", "memory"]),
    ("L04", "2210.03629", "ReAct 交织了哪两类痕迹？", ["reasoning", "acting", "推理", "行动", "action"]),
    ("L05", "2310.06117", "MemGPT 的记忆管理灵感来自什么？", ["operating systems", "操作系统", "OS"]),
    ("L06", "2402.09727", "RAPTOR 为检索构建了什么结构？", ["tree", "树", "recursive"]),
    ("L07", "2312.10997", "该 RAG survey 划分了哪几类 RAG？", ["naive", "advanced", "modular"]),
    ("L08", "2005.11401", "经典 RAG 论文的非参数记忆索引了什么语料？", ["Wikipedia", "维基"]),
    ("L09", "2305.14251", "Toolformer 让模型学会什么？", ["API", "tools", "工具"]),
    ("L10", "2212.10560", "Self-Instruct 如何减少人工标注？", ["self-generated", "bootstrapping", "自生成", "自身生成"]),
    ("L11", "2305.18290", "Let's Verify Step by Step 比较了哪两类奖励模型？", ["process", "outcome", "过程", "结果"]),
    ("L12", "2201.11903", "Chain-of-Thought prompting 提供什么以激发推理？", ["intermediate", "reasoning steps", "中间", "推理步骤"]),
    ("L13", "2305.10601", "Tree of Thoughts 相对 CoT 的扩展是什么？", ["multiple", "tree", "多条", "树"]),
    ("L14", "2401.04398", "Agent Laboratory 用 LLM agents 协助什么？", ["research", "研究"]),
    ("L15", "2310.08560", "FireAct 研究的是语言 agent 的什么训练方式？", ["fine-tuning", "微调"]),
    ("L16", "2406.04692", "该 survey 聚焦 RAG 与什么生成任务？", ["text generation", "文本生成"]),
    ("L17", "2308.09583", "LLM agents survey 讨论的能力维度含 memory 与？", ["tool", "planning", "工具", "规划"]),
    ("L18", "2402.01622", "检索增强对代码生成有何实证结论？", ["improves", "提升", "improve", "quality"]),
    ("L19", "2501.00663", "该 survey 讨论压缩什么缓存以利长上下文推理？", ["KV-Cache", "key-value", "KV cache", "KV缓存"]),
    ("L20", "2309.00267", "CoALA 框架组织 memory、action spaces 与？", ["decision", "决策"]),
]
lit = []
for tid, arx, prompt, golds in lit_qs:
    paper = next(p for p in PAPERS if p[0] == arx)
    snippet = f"arXiv:{paper[0]}\nTitle:{paper[1]}\nAbstract:{paper[2]}"
    lit.append({
        "id": tid, "track": "lit", "category": "literature", "prompt": prompt,
        "gold": {"must_any": golds, "abstain": False, "arxiv_id": arx},
        "rubric": "protocol_v2_fair", "arxiv_id": arx, "doi_or_arxiv": f"arXiv:{arx}",
        "amber_snippet": snippet,
    })
wjsonl(TASKS / "lit20.jsonl", lit)

# ---------- Programming ----------
prog = []

def add_prog(row):
    prog.append(row)

def concat_py_from_sandbox(sb: Path, cap_chars: int = 36000) -> str:
    parts, total = [], 0
    files = sorted([p for p in sb.rglob("*") if p.is_file() and p.suffix in {".py", ".md", ".toml", ".cfg", ".ini", ".txt"}])
    files.sort(key=lambda p: (0 if "src" in p.parts else 1, str(p)))
    for p in files:
        if any(x in p.parts for x in {".git", "tests", "test", "docs", ".github", "examples", "benchmarks"}):
            if p.name.lower() not in {"readme.md", "readme.rst"} and "test" in p.parts:
                continue
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        chunk = f"\n\n# ===== FILE: {p.relative_to(sb)} =====\n" + txt
        if total + len(chunk) > cap_chars:
            remain = cap_chars - total
            if remain > 200:
                parts.append(chunk[:remain]); total = cap_chars
            break
        parts.append(chunk); total += len(chunk)
    return "".join(parts) or "# empty"

def load_sha(sb: Path) -> str:
    for name in [".COMMIT_SHA", "COMMIT_SHA", ".sha"]:
        f = sb / name
        if f.exists():
            return f.read_text(encoding="utf-8", errors="replace").strip()[:64]
    return "unknown"

COACH_PATTERNS = [
    re.compile(r"(?m)^##\s*诚实出口\s*\n(?:.*\n)*?(?=^##|\Z)"),
    re.compile(r"(?m)^##\s*RESIDENT 纪律\s*\n(?:.*\n)*?(?=^##|\Z)"),
    re.compile(r"索引未覆盖时回答「无法定位」[^\n]*"),
    re.compile(r"索引未覆盖\s*→\s*「无法定位」[^\n]*"),
    re.compile(r"索引未覆盖时如实拒绝[^\n]*"),
    re.compile(r"不确定就诚实出口[^\n]*"),
    re.compile(r"回答「无法定位」，不要虚构[^\n]*"),
    re.compile(r"→「无法定位」，不要虚构[^\n]*"),
]

def strip_abstain_coaching(text: str) -> str:
    out = text
    for pat in COACH_PATTERNS:
        out = pat.sub("", out)
    # collapse excess blank lines
    out = re.sub(r"\n{3,}", "\n\n", out).strip() + "\n"
    return out

def extract_ledger_block(c_text: str) -> str:
    """Pull factual ledger/resident tables from C (after coaching strip)."""
    c = strip_abstain_coaching(c_text)
    chunks = []
    # keep markdown tables and RESIDENT bullet facts
    lines = c.splitlines()
    buf = []
    keep = False
    for ln in lines:
        if re.search(r"LEDGER|RESIDENT|账本|开工摘录|源码锚点|AMBER", ln) and not re.search(r"诚实出口|纪律", ln):
            keep = True
        if ln.startswith("## 任务"):
            keep = False
            buf = []
            continue
        if keep:
            buf.append(ln)
            if ln.strip() == "" and buf and any("|" in x for x in buf):
                chunks.append("\n".join(buf).strip()); buf = []; keep = False
    if buf:
        chunks.append("\n".join(buf).strip())
    # fallback: whole C minus task header
    if not chunks:
        body = re.sub(r"(?ms)^## 任务.*?(?=^## |\Z)", "", c).strip()
        chunks = [body] if body else [c[:1500]]
    block = "\n\n".join(chunks)
    return "【共享账本约定层·与 C 同源事实面】\n" + block[:3500] + "\n"

# A) github-ab 5
q_map = {
  "G1-key-derivation": ("在 itsdangerous 中，Signer.default_key_derivation 的正确默认值是什么？给出符号名、值、文件路径。",
                        {"mode": "locate", "must_any": ["django-concat"], "must_file_any": ["signer.py"]}),
  "G1-abstain-max-age-const": ("DEFAULT_SESSION_MAX_AGE 在 itsdangerous.session_policy 中的约定值是多少？若未覆盖请诚实拒答。",
                        {"mode": "abstain", "must_any": ["无法定位", "不存在", "没有该", "无此", "未覆盖", "not found"]}),
  "G2-fore-red": ("colorama 中 AnsiFore.RED / Fore.RED 的正确数值？给出符号、值、文件。",
                        {"mode": "locate", "must_any": ["31"], "must_file_any": ["ansi.py"]}),
  "G3-population-size": ("promptimal 优化器 population_size 的正确默认值？给出参数名、值、文件。",
                        {"mode": "locate", "must_any": ["5"], "must_file_any": ["main.py"]}),
  "G3-abstain-teleport": ("promptimal.quantum.teleport 中 DEFAULT_TELEPORT_TIMEOUT？若无此模块请拒答。",
                        {"mode": "abstain", "must_any": ["无法定位", "不存在", "没有该", "无此", "未覆盖", "not found"]}),
}
meta = {
 "G1-key-derivation": ("itsdangerous", "672971d66a2ef9f85151e53283113f33d642dabd", "https://github.com/pallets/itsdangerous"),
 "G1-abstain-max-age-const": ("itsdangerous", "672971d66a2ef9f85151e53283113f33d642dabd", "https://github.com/pallets/itsdangerous"),
 "G2-fore-red": ("colorama", "841634ed2a0da5d5ac2d867db533da8131266cb2", "https://github.com/tartley/colorama"),
 "G3-population-size": ("promptimal", "e03cbc1db19c7ec6c310605a9819e35c2baed023", "https://github.com/shobrook/promptimal"),
 "G3-abstain-teleport": ("promptimal", "e03cbc1db19c7ec6c310605a9819e35c2baed023", "https://github.com/shobrook/promptimal"),
}
for i, tid in enumerate(q_map, 1):
    pid = f"P{i:02d}"
    b = (GAB / "contexts" / f"{tid}-B.txt").read_text(encoding="utf-8", errors="replace")
    c = (GAB / "contexts" / f"{tid}-C.txt").read_text(encoding="utf-8", errors="replace")
    (CTX / f"{pid}_B.txt").write_text(b, encoding="utf-8")
    (CTX / f"{pid}_C.txt").write_text(c, encoding="utf-8")
    prompt, gold = q_map[tid]
    repo, sha, url = meta[tid]
    add_prog({
        "id": pid, "track": "prog", "category": gold["mode"], "prompt": prompt,
        "gold": gold, "rubric": "protocol_v2_fair",
        "repo": repo, "source_sha": sha, "repo_url": url, "source": "github-ab",
        "ctx_b": f"contexts/prog/{pid}_B.txt", "ctx_c": f"contexts/prog/{pid}_C.txt",
        "legacy_task_id": tid,
    })

# B) T1-T6
tqs = {
 "T1": ("核验窗口 WINDOW_SPAN_VERIFY 应恢复为多少？给出符号、值、文件。", {"mode":"locate","must_any":["1600"],"must_file_any":["constants.py"]}),
 "T2": ("honest_exit 中新增 is_cannot_locate 的判定语义是什么？指出文件与符号。", {"mode":"locate","must_any":["is_cannot_locate","无法定位"],"must_file_any":["honest_exit.py"]}),
 "T3": ("reject_placeholder_key 在什么情况下应返回 True（拒绝）？给出文件与符号。", {"mode":"locate","must_any":["reject_placeholder_key","PLACEHOLDER"],"must_file_any":["ops_guard.py"]}),
 "T4": ("按账本约定，WINDOW_FALLBACK_HEAD 正确值是多少？", {"mode":"locate","must_any":["800"],"must_file_any":["constants.py"]}),
 "T5": ("HONEST_EXIT_MARK 的约定字符串是什么？涉及哪些文件改动说明即可。", {"mode":"locate","must_any":["无法定位"],"must_file_any":["constants.py"]}),
 "T6": ("engine.quantum.teleport 的 DEFAULT_TELEPORT_TIMEOUT？若无请拒答。", {"mode":"abstain","must_any":["无法定位","不存在","没有该","无此","未覆盖","not found"]}),
}
for j, tid in enumerate(["T1","T2","T3","T4","T5","T6"], 6):
    pid = f"P{j:02d}"
    b = (TCTX / f"{tid}-B.txt").read_text(encoding="utf-8", errors="replace")
    c = (TCTX / f"{tid}-C.txt").read_text(encoding="utf-8", errors="replace")
    (CTX / f"{pid}_B.txt").write_text(b, encoding="utf-8")
    (CTX / f"{pid}_C.txt").write_text(c, encoding="utf-8")
    prompt, gold = tqs[tid]
    add_prog({
        "id": pid, "track": "prog", "category": gold["mode"], "prompt": prompt,
        "gold": gold, "rubric": "protocol_v2_fair",
        "repo": "amber-workbench-sandbox", "source_sha": "workbench-20261025",
        "repo_url": "local://deepseek-full-20261026", "source": "T1-T6",
        "ctx_b": f"contexts/prog/{pid}_B.txt", "ctx_c": f"contexts/prog/{pid}_C.txt",
        "legacy_task_id": tid,
    })

# C) gap-v1 6 — tightened golds (no bare .py / &)
gap_items = [
 ("N1_markupsafe_step1", "markupsafe", "https://github.com/pallets/markupsafe",
  "MarkupSafe 中 `_escape_inner` 对字符 '<' 应映射成什么实体？", ["&lt;", "lt;"], "_native.py"),
 ("N1_markupsafe_step2", "markupsafe", "https://github.com/pallets/markupsafe",
  "MarkupSafe escape 时 '&' 是否必须先替换？请依据上下文作答。", ["&amp;", "amp;"], "_native.py"),
 ("N2_iniconfig_step1", "iniconfig", "https://github.com/pytest-dev/iniconfig",
  "根据上下文，iniconfig 解析相关缺陷应改哪个模块/文件？给出路径关键词。", ["iniconfig", "_parse", "ini"], None),
 ("N2_iniconfig_step2", "iniconfig", "https://github.com/pytest-dev/iniconfig",
  "结合窄窗/全文，说明本步要修的行为要点（关键词即可）。", ["parse", "section", "key"], None),
 ("N3_dirty_equals_step1", "dirty-equals", "https://github.com/samuelcolvin/dirty-equals",
  "dirty-equals 本步缺陷相关的符号或文件名关键词是什么？", ["dirty_equals", "DirtyEquals", "IsStr"], None),
 ("N3_dirty_equals_step2", "dirty-equals", "https://github.com/samuelcolvin/dirty-equals",
  "结合上下文，本步修复应聚焦的断言/比较行为关键词？", ["equal", "DirtyEquals", "IsAny"], None),
]
for n, (stem, repo, url, prompt, golds, fhint) in enumerate(gap_items, 12):
    pid = f"P{n:02d}"
    sb = GAP1 / "sandboxes" / f"{stem}_B"
    win = GAP1 / "results" / f"{stem}_C_window.txt"
    brief = GAP1 / "results" / f"{stem}_brief.txt"
    if not sb.exists():
        sb = GAP1 / "sandboxes" / f"{stem}_C"
    btxt = concat_py_from_sandbox(sb)
    ctxt = win.read_text(encoding="utf-8", errors="replace") if win.exists() else btxt[:4000]
    if brief.exists():
        br = brief.read_text(encoding="utf-8", errors="replace")[:1500]
        ctxt = "【任务书】\n" + br + "\n\n" + ctxt
        btxt = "【任务书】\n" + br + "\n\n" + btxt
    (CTX / f"{pid}_B.txt").write_text(btxt, encoding="utf-8")
    (CTX / f"{pid}_C.txt").write_text(ctxt, encoding="utf-8")
    gold = {"mode": "locate", "must_any": golds}
    if fhint:
        gold["must_file_any"] = [fhint]
    add_prog({
        "id": pid, "track": "prog", "category": "locate", "prompt": prompt,
        "gold": gold, "rubric": "protocol_v2_fair",
        "repo": repo, "source_sha": load_sha(sb), "repo_url": url, "source": "gap-v1",
        "ctx_b": f"contexts/prog/{pid}_B.txt", "ctx_c": f"contexts/prog/{pid}_C.txt",
        "legacy_task_id": stem,
    })

# D) gap-v1-round2 6 — tightened
r2_items = [
 ("R1_blinker_step1", "blinker", "https://github.com/pallets-eco/blinker",
  "blinker 本步应关注的核心模块/符号关键词？", ["Signal", "signal", "blinker"]),
 ("R1_blinker_step2", "blinker", "https://github.com/pallets-eco/blinker",
  "结合上下文，blinker 第二步修复要点关键词？", ["connect", "send", "Signal"]),
 ("R2_zipp_step1", "zipp", "https://github.com/jaraco/zipp",
  "zipp 本步相关路径或 API 关键词？", ["zipp", "Path", "CompleteDirs"]),
 ("R2_zipp_step2", "zipp", "https://github.com/jaraco/zipp",
  "zipp 第二步应修改行为的关键词？", ["namelist", "open", "Path"]),
 ("R3_pyproject_hooks_step1", "pyproject-hooks", "https://github.com/pypa/pyproject-hooks",
  "pyproject-hooks 本步钩子/后端相关关键词？", ["build_backend", "hook", "Backend"]),
 ("R3_pyproject_hooks_step2", "pyproject-hooks", "https://github.com/pypa/pyproject-hooks",
  "第二步修复相关关键词？", ["prepare_metadata", "build_wheel", "hook"]),
]
for n, item in enumerate(r2_items, 18):
    stem, repo, url, prompt, golds = item
    pid = f"P{n:02d}"
    sb = GAP2 / "sandboxes" / f"{stem}_B"
    win = None
    for base in [GAP2 / "results", GAP2B / "results"]:
        cand = base / f"{stem}_C_window.txt"
        if cand.exists():
            win = cand; break
    brief = None
    for base in [GAP2 / "results", GAP2 / "tasks", GAP2B / "tasks", GAP2B / "results"]:
        cand = base / f"{stem}_brief.txt"
        if cand.exists():
            brief = cand; break
    btxt = concat_py_from_sandbox(sb) if sb.exists() else "# missing sandbox"
    ctxt = win.read_text(encoding="utf-8", errors="replace") if win and win.exists() else btxt[:4500]
    if brief and brief.exists():
        br = brief.read_text(encoding="utf-8", errors="replace")[:1500]
        ctxt = "【任务书】\n" + br + "\n\n" + ctxt
        btxt = "【任务书】\n" + br + "\n\n" + btxt
    (CTX / f"{pid}_B.txt").write_text(btxt, encoding="utf-8")
    (CTX / f"{pid}_C.txt").write_text(ctxt, encoding="utf-8")
    add_prog({
        "id": pid, "track": "prog", "category": "locate", "prompt": prompt,
        "gold": {"mode": "locate", "must_any": golds}, "rubric": "protocol_v2_fair",
        "repo": repo, "source_sha": load_sha(sb) if sb.exists() else "unknown",
        "repo_url": url, "source": "gap-v1-round2",
        "ctx_b": f"contexts/prog/{pid}_B.txt", "ctx_c": f"contexts/prog/{pid}_C.txt",
        "legacy_task_id": stem,
    })

# E) extras
extra = [
 ("P24", "itsdangerous", "672971d66a2ef9f85151e53283113f33d642dabd", "https://github.com/pallets/itsdangerous",
  "G1-key-derivation", "TimestampSigner 相关文件在其危险库中的路径关键词？", ["timed.py", "TimestampSigner"]),
 ("P25", "colorama", "841634ed2a0da5d5ac2d867db533da8131266cb2", "https://github.com/tartley/colorama",
  "G2-fore-red", "AnsiFore 类定义在哪个文件？", ["ansi.py", "AnsiFore"]),
 ("P26", "promptimal", "e03cbc1db19c7ec6c310605a9819e35c2baed023", "https://github.com/shobrook/promptimal",
  "G3-population-size", "optimizer 主入口文件路径关键词？", ["optimizer", "main.py"]),
]
reuse = {"P24": "P01", "P25": "P03", "P26": "P04"}
for pid, repo, sha, url, legacy, prompt, golds in extra:
    src = reuse[pid]
    shutil.copy(CTX / f"{src}_B.txt", CTX / f"{pid}_B.txt")
    shutil.copy(CTX / f"{src}_C.txt", CTX / f"{pid}_C.txt")
    add_prog({
        "id": pid, "track": "prog", "category": "locate", "prompt": prompt,
        "gold": {"mode": "locate", "must_any": golds}, "rubric": "protocol_v2_fair",
        "repo": repo, "source_sha": sha, "repo_url": url, "source": "github-ab-reuse",
        "ctx_b": f"contexts/prog/{pid}_B.txt", "ctx_c": f"contexts/prog/{pid}_C.txt",
        "legacy_task_id": legacy,
    })

more = [
 ("P27", "T1", "APPEND_ONLY_ENFORCE 在约定中应为 True 还是 False？", ["True", "true"], "locate"),
 ("P28", "T3", "ops key 校验函数名是什么？", ["reject_placeholder_key"], "locate"),
 ("P29", "T2", "cannot_locate 返回的 answer 字段约定文案？", ["无法定位"], "locate"),
 ("P30", "T6", "是否存在 engine.quantum 模块？请据上下文作答。", ["无法定位", "不存在", "没有该", "无此", "未覆盖"], "abstain"),
]
for pid, src_t, prompt, golds, mode in more:
    src_pid = {"T1":"P06","T2":"P07","T3":"P08","T4":"P09","T5":"P10","T6":"P11"}[src_t]
    shutil.copy(CTX / f"{src_pid}_B.txt", CTX / f"{pid}_B.txt")
    shutil.copy(CTX / f"{src_pid}_C.txt", CTX / f"{pid}_C.txt")
    add_prog({
        "id": pid, "track": "prog", "category": mode, "prompt": prompt,
        "gold": {"mode": mode, "must_any": golds}, "rubric": "protocol_v2_fair",
        "repo": "amber-workbench-sandbox", "source_sha": "workbench-20261025",
        "repo_url": "local://deepseek-full-20261026", "source": "T1-T6-reuse",
        "ctx_b": f"contexts/prog/{pid}_B.txt", "ctx_c": f"contexts/prog/{pid}_C.txt",
        "legacy_task_id": src_t,
    })

assert len(prog) == 30, len(prog)

# ---- Fairness pass on prog contexts ----
fair_log = []
for row in prog:
    pb = ROOT / row["ctx_b"]
    pc = ROOT / row["ctx_c"]
    b = pb.read_text(encoding="utf-8", errors="replace")
    c = pc.read_text(encoding="utf-8", errors="replace")
    c2 = strip_abstain_coaching(c)
    b2 = strip_abstain_coaching(b)
    golds = row["gold"].get("must_any") or []
    mode = row["gold"].get("mode")
    # For locate: if any primary gold missing from B, prepend shared ledger from C
    if mode == "locate":
        missing = [g for g in golds if g.casefold() not in b2.casefold()]
        if missing:
            ledger = extract_ledger_block(c)  # from original C before/after strip
            # avoid double-prepend
            if "【共享账本约定层" not in b2:
                b2 = ledger + "\n" + b2
                fair_log.append({"id": row["id"], "action": "prepend_ledger_to_B", "missing": missing})
            # re-check
            still = [g for g in golds if g.casefold() not in b2.casefold()]
            if still:
                # inject explicit fact lines for still-missing golds from C matches
                inject = []
                for g in still:
                    for ln in c2.splitlines():
                        if g.casefold() in ln.casefold() and ln.strip():
                            inject.append(ln.strip())
                            break
                if inject:
                    b2 = "【共享账本约定层·补齐金标事实】\n" + "\n".join(inject) + "\n\n" + b2
                    fair_log.append({"id": row["id"], "action": "inject_gold_lines", "lines": inject})
    # For abstain: ensure C no longer contains coaching; factual "无 X" rows OK
    if mode == "abstain":
        if c2 != c:
            fair_log.append({"id": row["id"], "action": "strip_coaching_C", "delta_chars": len(c)-len(c2)})
        if b2 != b and "诚实出口" in b:
            fair_log.append({"id": row["id"], "action": "strip_coaching_B", "delta_chars": len(b)-len(b2)})
    pb.write_text(b2, encoding="utf-8")
    pc.write_text(c2, encoding="utf-8")
    row["fairness_notes"] = [x for x in fair_log if x["id"] == row["id"]]

wjsonl(TASKS / "prog30.jsonl", prog)
(PARAMS / "fairness_log.json").write_text(json.dumps(fair_log, ensure_ascii=False, indent=2), encoding="utf-8")

# verify no gold-only-in-C for locate
issues = []
for row in prog:
    b = (ROOT / row["ctx_b"]).read_text(encoding="utf-8", errors="replace")
    c = (ROOT / row["ctx_c"]).read_text(encoding="utf-8", errors="replace")
    golds = row["gold"].get("must_any") or []
    if row["gold"].get("mode") == "locate":
        miss_b = [g for g in golds if g.casefold() not in b.casefold()]
        if miss_b and all(g.casefold() not in b.casefold() for g in golds):
            issues.append((row["id"], "ALL_gold_missing_B", miss_b))
    # coaching leftover?
    for tip in ["回答「无法定位」", "→「无法定位」", "## 诚实出口"]:
        if tip in c:
            issues.append((row["id"], "coach_left_C", tip))

meta_out = {
    "daily_ledger_chars": len(FULL_LEDGER),
    "daily_ledger_lines": len(LEDGER_LINES),
    "daily_noise_lines": 0,
    "daily_hist_lines": 0,
    "lit_full_chars": len(FULL_LIT),
    "n_daily": len(daily), "n_prog": len(prog), "n_lit": len(lit),
    "fairness_actions": len(fair_log),
    "remaining_issues": issues,
    "method_id": "amber-public-bench-20261027-r2-fair",
}
(PARAMS / "task_meta.json").write_text(json.dumps(meta_out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(meta_out, ensure_ascii=False, indent=2))
if issues:
    print("WARN remaining issues:", issues, file=sys.stderr)
print("OK fair tasks built")

# -*- coding: utf-8 -*-
"""插件：技能知识库（能力 "skills"）—— 装载 skills/*.md 方法论，模型可在会话中查询。

把三个安全研究方向（offensive-payloads / security-resource-map / pentest-killchain）
蒸馏为可直接调用的知识资产，作为只读工具挂在工具管道上（read_only，跳过授权）。
"""
import pathlib

from .. import config
from ..tools import ToolSpec

interface = "skills"

SKILLS_DIR = pathlib.Path(__file__).resolve().parent.parent / "skills"


def _load_all() -> dict[str, dict]:
    """扫描 skills/*.md，返回 {技能名: {"meta": {...}, "text": "..."}}"""
    skills = {}
    if not SKILLS_DIR.is_dir():
        return skills
    for f in sorted(SKILLS_DIR.glob("*.md")):
        try:
            text = f.read_text(encoding="utf-8")
        except OSError:
            continue
        meta: dict = {}
        body = text
        if text.startswith("---"):
            end = text.find("---", 3)
            if end != -1:
                head = text[3:end]
                for line in head.strip().splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        meta[k.strip()] = v.strip().strip('"')
                body = text[end + 3:].strip()
        skills[f.stem] = {"meta": meta, "text": body}
    return skills


def make_query(store: dict):
    """闭包：技能库在插件 setup 时捕获，ToolSpec.ctx 由管道统一注入不冲突。"""
    def _query(args, ctx):
        name = args.get("skill", "").strip()
        topic = args.get("topic", "").strip().lower()
        if name and name not in store:
            return f"[技能库] 未知技能: {name}，可用: {', '.join(sorted(store))}"
        if not store:
            return "[技能库] 空（skills/ 目录无内容）"
        if not topic:
            rows = []
            for n in sorted(store):
                meta = store[n]["meta"]
                rows.append(f"## {n}\n来源: {meta.get('source', '')}\n"
                            f"类型: {meta.get('type', '')}\n"
                            f"{store[n]['text'][:1400]}")
            return "\n\n".join(rows)[: config.MAX_TOOL_OUTPUT]
        text = store[name]["text"] if name else \
            "\n\n".join(store[n]["text"] for n in sorted(store))
        lines, hits = text.splitlines(), []
        for i, line in enumerate(lines):
            if topic in line.lower() or any(t in line.lower() for t in topic.split()):
                lo, hi = max(0, i - 1), min(len(lines), i + 3)
                hits.append("\n".join(lines[lo:hi]))
        if not hits:
            where = f"在 {name} 中" if name else "在技能库中"
            return f"[技能库] {where}未命中主题 '{topic}'"
        return "\n---\n".join(map(str.strip, hits))[: config.MAX_TOOL_OUTPUT]
    return _query


def setup(bus):
    store = _load_all()
    tools = bus.require("tools")
    tools.register(ToolSpec(
        name="skill_query",
        read_only=True,
        description=(
            "从内置技能知识库检索安全研究方向方法论。技能名 skill 可选值: "
            "offensive-payloads（web 漏洞与绕过）/ security-resource-map（安全资源导航）/ "
            "pentest-killchain（渗透全周期打法）。topic 为主题关键词（如 'WAF bypass' / 'AWS'）。"
        ),
        parameters={"skill": {"type": "string", "description": "技能名；省略则全库"},
                    "topic": {"type": "string", "description": "主题关键词"}},
        handler=make_query(store),
    ))
    bus.provide(interface, {"list": lambda: sorted(store),
                            "query": make_query(store)})
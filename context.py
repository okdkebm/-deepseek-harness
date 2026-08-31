# -*- coding: utf-8 -*-
"""上下文管理：估算 + 裁剪（dsh compaction 的轻量版）。

裁剪策略：保留 system + 最早的任务 user 消息 + 最近 N 条（工具结果优先），
中部折叠为占位行。真实"压缩"= 让模型把中段摘要成 1 条（接口已预留，成本高可关）。
"""
from . import config

_CTX_RESERVE = 2000  # 留给未裁剪输出的余量


def ctx_chars(messages: list[dict]) -> int:
    """粗略估算发送给模型的字符总量（中文约 1 字符 >= 1 token 下界）。"""
    total = 0
    for m in messages:
        total += len(m.get("content") or "")
        for c in m.get("tool_calls", []):
            total += len(c["function"]["name"]) + len(c["function"]["arguments"])
    return total


def trim_messages(messages: list[dict], max_chars: int = None) -> list[dict]:
    """超出上限时折叠中段。不修改会话日志，只裁剪本次发送给模型的副本。"""
    max_chars = max_chars or config.MAX_CTX_CHARS
    if ctx_chars(messages) <= max_chars:
        return messages

    head, tail = messages[:2], messages[2:]           # system + 最早 user
    keep, acc = [], 0
    for m in tail:
        cost = len(m.get("content") or "")
        if keep and acc + cost > max_chars - _CTX_RESERVE:
            break
        keep.append(m)
        acc += cost

    head.append({"role": "user",
                 "content": f"(【上下文已裁剪】中段 {len(tail) - len(keep)} 条历史省略，"
                            "直接继续后续任务，不要回问)"})
    return head + keep


def summarize(messages: list[dict], model=None) -> str:
    """预留：真实压缩 = 调模型把 messages 压成摘要。
    默认关闭（本地小模型摘要质量不稳且耗时），需要时由 runner 注入 model 开启。"""
    raise NotImplementedError("真实压缩需注入模型驱动，当前使用裁剪策略即可。")
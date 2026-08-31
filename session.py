# -*- coding: utf-8 -*-
"""会话日志：append-only JSONL 事件流（dsh SessionEvent 的本地落点）。

- 每次模型可见的事件（user/assistant/tool/tool_result）都追加落盘。
- resume: 读取历史事件 -> 重建 messages -> 继续同一会话。
- fork:  复制历史到新会话 id -> 在新会话中派生子任务（保留上文、不改原文）。
"""
import json
import pathlib
import time
import uuid


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def new_id() -> str:
    return time.strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:6]


class Session:
    def __init__(self, sid: str, path: pathlib.Path, events: list[dict] | None = None):
        self.id = sid
        self.path = path
        self._events = events or []

    # ---- 创建 / 恢复 / 分叉 ----
    @classmethod
    def create(cls, sessions_dir: pathlib.Path) -> "Session":
        """新建会话：立刻落盘一条 meta 事件（空会话也持久化，可被 resume/fork）。"""
        sid = new_id()
        path = sessions_dir / f"{sid}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        obj = cls(sid, path)
        obj.append({"type": "meta", "content": "created"})
        return obj

    @classmethod
    def resume(cls, sid: str, sessions_dir: pathlib.Path) -> "Session":
        path = sessions_dir / f"{sid}.jsonl"
        if not path.is_file():
            raise FileNotFoundError(f"会话不存在: {sid}（用 --list 查看可用会话）")
        events = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                events.append(json.loads(line))
        return cls(sid, path, events)

    def fork(self, sessions_dir: pathlib.Path) -> "Session":
        """分叉：新 id、继承全部历史事件，独立落盘。"""
        child = Session.create(sessions_dir)
        for e in self._events:
            child.append(e)
        return child

    # ---- 追加（append-only 落盘）----
    def append(self, event: dict) -> None:
        event = {"ts": _now(), **event}
        self._events.append(event)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    # ---- 重建 messages ----
    def build_messages(self, system: str) -> list[dict]:
        msgs = [{"role": "system", "content": system}]
        for e in self._events:
            t = e.get("type")
            if t == "user":
                msgs.append({"role": "user", "content": e.get("content", "")})
            elif t == "assistant":
                m = {"role": "assistant", "content": e.get("content")}
                if e.get("tool_calls"):
                    m["tool_calls"] = self._restore_calls(e["tool_calls"])
                msgs.append(m)
            elif t == "tool_result":
                msgs.append({"role": "tool", "tool_call_id": e.get("tool_call_id"),
                             "content": e.get("content", "")})
        return msgs

    @staticmethod
    def _restore_calls(calls: list) -> list:
        """事件存档的 tool_calls 与 OpenAI 格式对齐。"""
        return [{"id": c["id"],
                 "type": "function",
                 "function": {"name": c["name"],
                              "arguments": json.dumps(c["arguments"], ensure_ascii=False)}}
                for c in calls]

    # ---- 元信息 ----
    def summary(self) -> str:
        k = len(self._events)
        first = next((e.get("content", "") for e in self._events
                      if e.get("type") == "user"), "")
        first = (first[:40] + "…") if len(first) > 40 else first
        return f"{self.id}  事件数={k:<3}  首轮任务: {first}"

    @property
    def events(self) -> list[dict]:
        return list(self._events)


def list_sessions(sessions_dir: pathlib.Path) -> list[pathlib.Path]:
    if not sessions_dir.is_dir():
        return []
    return sorted(sessions_dir.glob("*.jsonl"), reverse=True)
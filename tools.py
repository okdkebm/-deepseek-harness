# -*- coding: utf-8 -*-
"""工具注册表 + 执行管道（dsh tool pipeline 的本地落点）。

执行链路：授权闸门(guard) -> 执行 handler -> 结果规范化 -> 截断回填。
模型永远收到稳定的 {ok, output 或 error} 结构，失败也回填，让模型能自我纠正。
"""
import json
import pathlib
from dataclasses import dataclass, field
from typing import Callable, Optional

from . import config
from .guard import Guard


@dataclass
class ToolContext:
    """传给 handler 的运行时上下文：沙箱 + 工作区根。"""
    guard: Guard
    workspace: pathlib.Path

    def resolve(self, path: str) -> pathlib.Path:
        return self.guard.resolve_in_workspace(path)


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict
    handler: Callable
    required: tuple = ()
    read_only: bool = False
    ctx: Optional[ToolContext] = field(default=None, repr=False)

    def to_schema(self) -> dict:
        return {"type": "function", "function": {
            "name": self.name,
            "description": self.description,
            "parameters": {"type": "object",
                           "properties": self.parameters,
                           "required": list(self.required)},
        }}


class ToolRegistry:
    """注册/执行。execute 的入参是模型返回的原始参数文本。"""

    def __init__(self, guard: Guard):
        self._tools: dict[str, ToolSpec] = {}
        self.ctx = ToolContext(guard=guard, workspace=guard.workspace)

    def register(self, spec: ToolSpec) -> None:
        spec.ctx = self.ctx
        self._tools[spec.name] = spec

    def specs(self) -> list[dict]:
        return [t.to_schema() for t in self._tools.values()]

    def names(self) -> list[str]:
        return sorted(self._tools)

    def execute(self, name: str, args: dict) -> dict:
        spec = self._tools.get(name)
        if spec is None:
            return {"ok": False, "output": f"[错误] 未知工具: {name}"}
        # 1) 授权闸门
        if not spec.ctx.guard.check(name, args, spec.read_only):
            return {"ok": False, "output": f"[已拒绝] 工具 {name} 未获授权执行"}
        # 2) 执行 + 失败规范化
        try:
            raw = spec.handler(args, spec.ctx)
        except PermissionError as e:
            return {"ok": False, "output": f"[沙箱拦截] {e}"}
        except Exception as e:  # noqa: BLE001 —— 出错必须回填给模型纠错
            return {"ok": False, "output": f"[执行失败] {type(e).__name__}: {e}"}
        # 3) 截断回填（防爆上下文），保留足够的错误上下文
        text = str(raw)
        if len(text) > config.MAX_TOOL_OUTPUT:
            text = text[: config.MAX_TOOL_OUTPUT] + "\n...[过长已截断]"
        return {"ok": True, "output": text}


def run_tool_chain(registry: ToolRegistry, name: str, args_text: str) -> dict:
    """CLI/runner 统一入口：解析 JSON 参数 -> 走管道。"""
    try:
        args = json.loads(args_text) if args_text.strip() else {}
    except json.JSONDecodeError as e:
        return {"ok": False, "output": f"[参数解析失败] {e}: {args_text}"}
    if not isinstance(args, dict):
        return {"ok": False, "output": f"[参数错误] 期望对象，得到 {type(args).__name__}"}
    return registry.execute(name, args)
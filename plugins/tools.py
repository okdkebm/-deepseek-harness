# -*- coding: utf-8 -*-
"""插件：工具管道（能力 "tools"）—— 内置工具 + 子代理 spawn。

依赖：guard（沙箱）、model + session（供子代理派生）。
"""
from .. import config
from ..tools import ToolRegistry
from ..tools_builtin import register_builtin_tools

interface = "tools"

SYSTEM = config.DEFAULT_SYSTEM.format(workspace=config.WORKSPACE)


def setup(bus):
    guard = bus.require("guard")
    registry = ToolRegistry(guard)

    def spawn_fn(sargs, sctx):
        """子代理：独立新会话跑子任务，结论回填父模型（子代理不再 spawn 防失控）。"""
        from ..runner import AgentRunner
        model = bus.require("model")
        session_api = bus.require("session")
        child = session_api["create"]()
        child_registry = ToolRegistry(sctx.guard)
        register_builtin_tools(child_registry)
        sub = AgentRunner(model, child_registry, child,
                          SYSTEM, max_steps=5, verbose=False)
        print(f"  [子代理] 新会话 {child.id} 执行子任务…")
        return "[子代理结论] " + sub.run(sargs.get("instruction", ""))

    register_builtin_tools(registry, spawn_fn=spawn_fn)
    bus.provide(interface, registry)
# -*- coding: utf-8 -*-
"""插件：标准 Agent 循环（能力 "loop"）—— full turn/step 工具循环。

消费能力：model(必选) session(必选) tools(必选) context(可选)。
可选能力缺失不影响启动：没 context 就发全量历史。
"""
interface = "loop"
MODE = "standard"


def setup(bus):
    from ..runner import AgentRunner
    model = bus.require("model")
    session_api = bus.require("session")
    registry = bus.require("tools")

    def trim(messages):
        """动态查找可选能力：/disable context 后立即失效 -> 发送全量。"""
        ctx = bus.find("context")
        return ctx["trim"](messages) if ctx else messages

    def create(system_prompt, session=None):
        """返回 (loop, session)：session 供 cli 打印/绑定；minimal 循环返回 (loop, None)。"""
        session = session or session_api["create"]()
        return (AgentRunner(model, registry, session, system_prompt,
                            trim_fn=trim, max_steps=10), session)

    bus.provide(interface, {"mode": MODE, "create": create})
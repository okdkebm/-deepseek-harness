# -*- coding: utf-8 -*-
"""插件：极简 Agent 循环（能力 "loop"）—— 单步直答，不调用任何工具。

与 loop_standard 提供同一接口，可直接替换：命令行 --loop minimal 即可切换。
这证明"主循环本身可替换"（dsh 四种模式同构）。
"""
interface = "loop"
MODE = "minimal"


def setup(bus):
    model = bus.require("model")

    class MinimalLoop:
        def __init__(self, system_prompt):
            self.system = system_prompt

        def run(self, task: str, max_steps=None) -> str:
            msgs = [{"role": "system", "content": self.system},
                    {"role": "user", "content": task}]
            try:
                msg = model.chat(msgs, tools=[])      # 永不调用工具
            except Exception as e:                    # noqa: BLE001
                return f"[模型错误] {e}"
            return (msg.get("content") or "(无输出)").strip()

    def create(system_prompt, session=None):
        return (MinimalLoop(system_prompt), None)

    bus.provide(interface, {"mode": MODE, "create": create})
# -*- coding: utf-8 -*-
"""Agent Runner：turn/step 主循环（dsh Agent Loop 的本地落点）。

每个 turn 内执行若干 step，直到模型不再请求工具：
  写 user 事件 -> 发模型（可裁剪）-> 写 assistant 事件
   -> 有 tool_calls? 逐个走工具管道 -> 写 tool_result 事件 -> 继续
   -> 无 tool_calls? 完成

上下文裁剪由 context 插件注入 trim_fn；未装该插件（or 已被卸载）则发送全量。
"""
from .session import Session
from .tools import ToolRegistry, run_tool_chain


class AgentRunner:
    def __init__(self, model, registry: ToolRegistry,
                 session: Session, system_prompt: str,
                 max_steps: int = 10, verbose: bool = True,
                 trim_fn=None):
        self.model = model
        self.registry = registry
        self.session = session
        self.system_prompt = system_prompt
        self.max_steps = max_steps
        self.verbose = verbose
        self.trim = trim_fn or (lambda msgs: msgs)

    def _log(self, text: str) -> None:
        if self.verbose:
            print(text)

    def run(self, task: str, max_steps: int | None = None) -> str:
        session = self.session
        session.append({"type": "user", "content": task})
        max_steps = max_steps or self.max_steps
        self._log(f"[会话] {session.id}  模型: {self.model.name()}")

        for step in range(1, max_steps + 1):
            messages = self.trim(session.build_messages(self.system_prompt))
            self._log(f"[step {step}] 调用模型…")

            try:
                msg = self.model.chat(messages, self.registry.specs())
            except Exception as e:  # noqa: BLE001 —— 网络/协议错误直接暴露
                self._log(f"[模型错误] {e}")
                return f"[模型调用失败] {e}"

            # 记录 assistant 事件（含 or 不含 tool_calls）
            session.append({"type": "assistant", "content": msg.get("content"),
                            "tool_calls": msg.get("tool_calls")})

            calls = msg.get("tool_calls") or []
            if not calls:
                answer = (msg.get("content") or "").strip() or "(模型无输出)"
                return answer

            for c in calls:
                args_text = self._args_to_text(c.get("arguments"))
                self._log(f"  [工具] {c['name']}({args_text})")
                result = run_tool_chain(self.registry, c["name"], args_text)
                if not result["ok"]:
                    self._log(f"    -> {result['output'][:160]}")
                session.append({"type": "tool_result",
                                "tool_call_id": c["id"],
                                "content": result["output"]})

        self._log(f"[警告] 达到最大 step 数 {max_steps}")
        return "[达到最大 step 数，终止]"

    @staticmethod
    def _args_to_text(arguments) -> str:
        if isinstance(arguments, dict):
            import json
            return json.dumps(arguments, ensure_ascii=False)
        return str(arguments)
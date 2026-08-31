# -*- coding: utf-8 -*-
"""harness —— 万物可插件的本地 Agent 马具（零依赖、零成本，接近 deepseek-harness）。

架构 = 无特权核心 + 插件总线（dsh "Everything is a plugin" 的本地落点）：
  核心（~150 行，无特权）
    bus.py    ServiceBus —— provide/find/require 服务 + 事件 + 按插件卸载
    host.py   PluginHost —— 动态 import 插件、setup/teardown、运行时装卸
  能力（全部是插件，装配即用、可替换、可装卸）
    guard          安全守卫（ask/allow/deny + 工作区沙箱）
    model/mock     模型驱动（任意 OpenAI 兼容端点 / Mock 自测）
    session        会话日志（append-only JSONL + resume/fork）
    context        上下文裁剪（可选能力，卸载后发全量历史）
    tools          工具管道（内置工具 + spawn 子代理）
    loop_standard / loop_minimal   主循环（可替换）
    cli            REPL + /enable /disable /plugins 运行时命令
    acp           JSON-RPC 2.0 over TCP 服务（远程驱动总线 / 异步任务 / 事件推送）

验证过的关键属性（dsh 能力矩阵）：
  - 循环可替换：--loop minimal 单步直答，同接口即换
  - 能力可选：--plugin-off context 或 /disable context，缺能力照常运行
  - 运行时可装卸：/disable 后能力立即从总线移除，依赖方动态降级
  - 服务化：--serve --port 5213 起 ACP，客户端远程建会话/跑任务/装卸插件/收 task.done
  - 模型零成本可换：LLM_BASE_URL 指向 Ollama(localhost) 或 OpenRouter(:free)
"""

__version__ = "0.3.0"
# -*- coding: utf-8 -*-
"""CLI：纯装配器 —— 只负责"装哪些插件 + 启动"，不持有任何能力。

万物可插件：模型/循环/工具/守卫/会话/上下文/CLI 全是插件；核心（cli 装配层）
零特权。运行时可用 /enable、/disable 装卸插件，卸载的能力立即失效（动态查找）。

用法示例：
  python -m harness "帮我看看当前目录"               # 本地模型（默认 Ollama）
  python -m harness --mock "自测"                    # 无模型全链路自测
  python -m harness --loop minimal "你好"            # 换成极简循环（单步直答）
  python -m harness --plugin-off context ...         # 初始禁用某插件（能力可选）
  python -m harness --plugins                        # 查看插件与能力
  python -m harness --resume <ID> "继续"  /  --fork <ID> "新方向"
"""
import argparse
import sys

from . import config
from .host import PluginHost


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="harness",
                                description="本地 Agent Harness（万物可插件，接近 deepseek-harness）")
    p.add_argument("task", nargs="?", help="任务描述；省略则进入交互循环")
    p.add_argument("-t", "--task", dest="task2", help="同 task")
    p.add_argument("--mock", action="store_true", help="用 Mock 模型插件（不连端点，authz 强制 allow）")
    p.add_argument("--loop", choices=["standard", "minimal"], default="standard",
                   help="选择主循环插件（循环可替换的核心演示）")
    p.add_argument("--plugin-off", metavar="NAME", action="append", default=[],
                   help="初始禁用的插件（可多次），如 context / tools")
    p.add_argument("--plugins", action="store_true", help="查看已装插件与总线能力后退出")
    p.add_argument("--authz", choices=["allow", "ask", "deny"], help="授权模式，覆盖 DSH_AUTHZ")
    p.add_argument("--model", help="模型名，覆盖 LLM_MODEL")
    p.add_argument("--base-url", help="OpenAI 兼容端点，覆盖 LLM_BASE_URL")
    p.add_argument("--api-key", help="API Key，覆盖 LLM_API_KEY")
    p.add_argument("--resume", metavar="ID", help="恢复历史会话")
    p.add_argument("--fork", metavar="ID", help="从历史会话分叉出新会话")
    p.add_argument("--once", action="store_true", help="执行单次后退出")
    p.add_argument("--serve", action="store_true",
                   help="以 ACP 服务模式启动（JSON-RPC over TCP，供远程客户端驱动）")
    p.add_argument("--port", type=int, default=5213, help="ACP 服务端口（默认 5213）")
    p.add_argument("--host", default="127.0.0.1", help="ACP 监听地址（默认 127.0.0.1）")
    return p


def assemble_host(args, serve_mode: bool = False) -> PluginHost:
    """按依赖序装配插件集（顺序即 setup 顺序）。serve_mode 用 ACP 插件替代 REPL。"""
    host = PluginHost()
    # 先装与调用顺序无关的底座：guard -> session
    for name in ("guard", "session"):
        host.install(name)
    # 模型：mock 透视替换真实端点插件
    host.install("mock" if args.mock else "model")
    # 可选能力：context（卸载后循环发全量历史）
    host.install("context")
    # 工具依赖 guard/model/session
    host.install("tools")
    # 技能知识库（只读工具 skill_query，依赖 tools）
    host.install("skills")
    # 主循环可替换
    host.install(f"loop_{args.loop}")
    # 初始禁用
    for name in args.plugin_off:
        if host.uninstall(name):
            print(f"[装配] 已禁用插件: {name}")
    # 面向方式：REPL 或 ACP 服务；两者都需要 host 引用做运行时可装卸
    host.bus.host = host
    host.install("acp" if serve_mode else "cli")
    return host


def attach_overrides(args) -> None:
    """CLI 参数覆盖 config（须在装配 host 之前）。"""
    if args.mock:
        config.AUTHZ = "allow"          # mock 不自测联机交互审批
    if args.authz:
        config.AUTHZ = args.authz
    if args.model:
        config.MODEL = args.model
    if args.base_url:
        config.BASE_URL = args.base_url
    if args.api_key:
        config.API_KEY = args.api_key


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    attach_overrides(args)

    if args.plugins:
        tmp = assemble_host(args)       # 只装配到 loop，展示总览
        print(tmp.describe())
        return 0

    host = assemble_host(args, serve_mode=args.serve)
    if args.serve:
        acp_api = host.bus.require("acp")
        return acp_api["serve"](host.bus, args.host, args.port)

    cli_api = host.bus.require("cli")
    return cli_api["main"](args)


if __name__ == "__main__":
    sys.exit(main())
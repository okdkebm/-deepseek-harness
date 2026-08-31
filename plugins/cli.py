# -*- coding: utf-8 -*-
"""插件：CLI（能力 "cli"）—— 会话创建/多轮 REPL/运行时插件装卸命令。

交互命令：
  /plugins          查看已装插件与总线能力
  /enable  <name>   运行时安装插件（如 context —— 裁剪立即生效）
  /disable <name>   运行时卸载插件（能力立即从总线移除）
  /help /quit
"""
interface = "cli"


def setup(bus):
    from .. import config

    loop_api = bus.require("loop")
    session_api = bus.require("session")
    host = bus.host                          # 装配器在 install(cli) 前注入

    SYSTEM = config.DEFAULT_SYSTEM.format(workspace=config.WORKSPACE)

    def run_once(loop, task: str) -> None:
        final = loop.run(task)
        print(f"\n[完成] {final}")

    def handle_plugin_cmd(line: str) -> str | None:
        """处理 /命令；返回提示文本，非命令返回 None。"""
        parts = line.strip().split(maxsplit=1)
        cmd, arg = parts[0].lower(), parts[1] if len(parts) > 1 else ""
        if cmd == "/plugins":
            return host.describe()
        if cmd == "/enable":
            if not arg:
                return "用法: /enable <插件名>"
            try:
                host.install(arg)
            except Exception as e:  # noqa: BLE001
                return f"[错误] {e}"
            return f"[插件] 已启用 {arg}，能力接入总线（依赖方下次任务动态生效）"
        if cmd == "/disable":
            if not arg:
                return "用法: /disable <插件名>"
            if not host.uninstall(arg):
                return f"[错误] 无法禁用 {arg}（不存在或不可卸载）"
            return f"[插件] 已禁用 {arg}，其能力已从总线移除"
        if cmd == "/help":
            return "/plugins | /enable <名> | /disable <名> | /quit"
        return None

    def repl(loop) -> int:
        print(f"（循环模式: {loop_api['mode']} | /help | /quit）")
        while True:
            try:
                line = input("\n你: ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line:
                continue
            if line.lower() in ("quit", "exit", "q"):
                break
            if line.startswith("/"):
                note = handle_plugin_cmd(line)
                if note:
                    print(note)
                continue
            run_once(loop, line)
        return 0

    def main(args) -> int:
        session = None
        if args.fork:
            parent = session_api["resume"](args.fork)
            session = session_api["fork"](parent)
            print(f"[会话] 从 {parent.id} 分叉 -> {session.id}")
        elif args.resume:
            session = session_api["resume"](args.resume)
            print(f"[会话] 恢复 {session.id}")

        loop, session = loop_api["create"](SYSTEM, session=session)
        if session is not None and not (args.fork or args.resume):
            print(f"[会话] 新建 {session.id}   （之后可用 --resume {session.id} 恢复）")

        task = args.task or args.task2
        if task:
            run_once(loop, task)
        if not args.once:
            return repl(loop)
        return 0

    bus.provide(interface, {"main": main})
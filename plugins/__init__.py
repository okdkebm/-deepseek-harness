# -*- coding: utf-8 -*-
"""插件包。每个插件 = 一个模块，约定 setup(bus) 安装、可选 teardown(bus) 拆卸。

插件装配顺序（由 cli 决定）：guard -> model/mock -> session -> context -> tools -> loop -> cli。
能力（Service 接口）约定：
  "guard"    Guard 实例（with resolve_in_workspace / check）
  "model"    模型驱动（.chat(messages, tools) / .name）
  "session"  会话工厂 dict{dir, create, resume, fork, list}
  "context"  上下文工具 dict{trim, chars}
  "tools"    ToolRegistry 实例
  "loop"     循环工厂 dict{mode, create(system) -> .run(task, max_steps)}
  "cli"      CLI 入口 dict{run_once, repl}
"""
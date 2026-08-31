# -*- coding: utf-8 -*-
"""内置工具：文件读写 / 列目录 / 执行命令 / 派生子任务。

read_only=True 的工具跳过授权询问；写与执行受 guard 分级管控。
"""
import subprocess

from . import config
from .tools import ToolRegistry, ToolSpec


def _list_dir(args, ctx):
    p = ctx.resolve(args.get("path", "."))
    if not p.is_dir():
        raise FileNotFoundError(f"不是目录: {p}")
    rows = []
    for f in sorted(p.iterdir()):
        tag = "dir " if f.is_dir() else "file"
        rows.append(f"{tag}\t{f.name}")
    return "\n".join(rows) or "(空目录)"


def _read_file(args, ctx):
    p = ctx.resolve(args["path"])
    if not p.is_file():
        raise FileNotFoundError(f"文件不存在: {p}")
    if p.stat().st_size > 200_000:
        return f"(文件过大 {p.stat().st_size}B，仅读前 200KB)" + \
               p.read_text(encoding="utf-8", errors="ignore")[:200_000]
    return p.read_text(encoding="utf-8", errors="ignore")


def _write_file(args, ctx):
    p = ctx.resolve(args["path"])
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(args["content"], encoding="utf-8")
    return f"已写入 {len(args['content'])} 字符到 {p}"


def _run_command(args, ctx):
    cmd = args["cmd"]
    r = subprocess.run(cmd, shell=True, cwd=str(ctx.workspace),
                       capture_output=True, text=True,
                       timeout=config.CMD_TIMEOUT)
    out = (r.stdout or "") + (r.stderr or "")
    return out if out.strip() else f"(退出码 {r.returncode}，无输出)"


def register_builtin_tools(registry: ToolRegistry, spawn_fn=None) -> None:
    registry.register(ToolSpec(
        name="list_dir", read_only=True,
        description="列出目录内容",
        parameters={"path": {"type": "string", "description": "目录路径（相对工作区或绝对路径）"}},
        handler=_list_dir,
    ))
    registry.register(ToolSpec(
        name="read_file", read_only=True,
        description="读取文本文件内容",
        parameters={"path": {"type": "string", "description": "文件路径"}},
        required=("path",),
        handler=_read_file,
    ))
    registry.register(ToolSpec(
        name="write_file",
        description="写入文本到文件（覆盖）",
        parameters={"path": {"type": "string"}, "content": {"type": "string"}},
        required=("path", "content"),
        handler=_write_file,
    ))
    registry.register(ToolSpec(
        name="run_command",
        description="在 WORKSPACE 下执行 shell 命令并返回输出（只读命令优先）",
        parameters={"cmd": {"type": "string"}},
        required=("cmd",),
        handler=_run_command,
    ))
    if spawn_fn is not None:
        registry.register(ToolSpec(
            name="spawn_task",
            description="派生子代理在一个全新会话中执行独立子任务，结果回填给你（用于并行子任务/长任务切分）",
            parameters={"instruction": {"type": "string", "description": "给子代理的独立任务描述"}},
            required=("instruction",),
            handler=spawn_fn,
        ))
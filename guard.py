# -*- coding: utf-8 -*-
"""安全守卫：dsh 沙箱思想的本地落点。

1) 工作区沙箱：读写路径必须 resolve 后位于 WORKSPACE 内（防目录逃逸）。
2) 授权分级：allow（写入/执行直接放行）/ ask（逐个询问）/ deny（一律拒绝）。
   只读类工具（读文件/列目录）永远放行——与 dsh workspace-write 策略同构。
"""
import pathlib


class Guard:
    def __init__(self, mode: str, workspace: pathlib.Path):
        mode = (mode or "ask").strip().lower()
        if mode not in ("allow", "ask", "deny"):
            raise ValueError(f"非法授权模式: {mode}（allow|ask|deny）")
        self.mode = mode
        self.workspace = pathlib.Path(workspace).resolve()

    def resolve_in_workspace(self, path: str) -> pathlib.Path:
        """解析模型给的路径；越出工作区则抛 PermissionError。"""
        raw = pathlib.Path(path.strip())
        p = (self.workspace / raw).resolve() if not raw.is_absolute() else raw.resolve()
        if p != self.workspace:
            try:
                p.relative_to(self.workspace)
            except ValueError:
                raise PermissionError(f"路径越出工作区沙箱，已拒绝: {p}")
        return p

    def check(self, tool_name: str, args: dict, read_only: bool) -> bool:
        """工具执行前的授权闸门。返回 True=放行，False=拒绝。"""
        if read_only:
            return True
        if self.mode == "deny":
            print(f"  [守卫] 拒绝（deny 模式）：{tool_name}({args})")
            return False
        if self.mode == "allow":
            return True
        try:
            ans = input(f"  [守卫] 批准执行 {tool_name}({args}) ? [y/N] ").strip().lower()
            return ans in ("y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False
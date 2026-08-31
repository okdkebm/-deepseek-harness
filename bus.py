# -*- coding: utf-8 -*-
"""ServiceBus：无特权核心的"接线板"（dsh Capability Seam 的本地落点）。

核心不持有任何能力，只做两件事：
  1. 服务注册/查找 —— 插件 provide 能力，其他插件 find/require 消费能力
  2. 事件发布/订阅 —— 插件之间解耦通信
任何接口缺失都不影响核心本身运行；能力可选 = bus.find 可返回缺省。
"""
from dataclasses import dataclass


class PluginError(RuntimeError):
    """插件装配错误（能力缺失/冲突等）"""


@dataclass
class ServiceEntry:
    impl: object       # 服务实现
    owner: str = ""    # 提供者（插件全名），用于卸载清理
    optional: bool = False


@dataclass
class ListenerEntry:
    fn: callable
    owner: str = ""


class ServiceBus:
    def __init__(self, host=None):
        self._providers: dict[str, ServiceEntry] = {}
        self._listeners: dict[str, list[ListenerEntry]] = {}
        self._owner: str = ""      # 当前正在执行 setup 的插件名（隐式归属）
        self.host = host           # 装配器引用（插件需要时可取）

    # ---- 服务：注册 / 查找 ----
    def provide(self, interface: str, impl, optional: bool = False) -> None:
        """提供一项能力。后注册覆盖先注册（最后安装的插件生效）。"""
        self._providers[interface] = ServiceEntry(impl, self._owner, optional)

    def find(self, interface: str, default=None):
        """可选能力：缺失返回 default，不报错。"""
        e = self._providers.get(interface)
        return e.impl if e else default

    def require(self, interface: str):
        """必选能力：缺失抛出 PluginError。"""
        e = self._providers.get(interface)
        if e is None:
            raise PluginError(f"所需能力缺失: {interface}（请启用对应插件）")
        return e.impl

    def has(self, interface: str) -> bool:
        return interface in self._providers

    def interface_names(self) -> list[str]:
        return sorted(self._providers)

    # ---- 事件：发布 / 订阅 / 退订 ----
    def on(self, event: str, fn) -> None:
        self._listeners.setdefault(event, []).append(ListenerEntry(fn, self._owner))

    def off(self, event: str, fn) -> None:
        """退订单个监听（连接断开时使用）。"""
        ents = self._listeners.get(event)
        if not ents:
            return
        keep = [e for e in ents if e.fn is not fn]
        if keep:
            self._listeners[event] = keep
        else:
            self._listeners.pop(event, None)

    def emit(self, event: str, **payload) -> None:
        for ent in list(self._listeners.get(event, [])):
            ent.fn(**payload)

    def inventory(self) -> dict[str, list[str]]:
        """按插件归属列出能力：{owner: [interface, ...]}。"""
        inv: dict[str, list[str]] = {}
        for k, e in self._providers.items():
            inv.setdefault(e.owner or "?", []).append(k)
        return inv

    # ---- 卸载清理：按插件归属回收其全部注册 ----
    def drop_owner(self, owner: str) -> None:
        if owner:
            self._providers = {k: v for k, v in self._providers.items()
                               if v.owner != owner}
            for ev, ents in list(self._listeners.items()):
                keep = [e for e in ents if e.owner != owner]
                if keep:
                    self._listeners[ev] = keep
                else:
                    self._listeners.pop(ev, None)

    def summary(self) -> str:
        """形如  model=ChatModel, tools=ToolRegistry, ..."""
        return ", ".join(f"{k}={type(v.impl).__name__}"
                         for k, v in sorted(self._providers.items()))
# -*- coding: utf-8 -*-
"""PluginHost：装配器（dsh 插件生命周期 的本地落点）。

插件约定：特定模块内的 setup(bus) = 安装；可选 teardown(bus) = 拆卸。
核心本身无特权，只有"动态 import + setup + 按归属清理"这一种机械动作。
"""
import importlib
from dataclasses import dataclass

from .bus import PluginError, ServiceBus


@dataclass
class PluginMeta:
    name: str               # 短名，如 "tools"
    module: object          # 已加载的插件模块


class PluginHost:
    def __init__(self, package: str = "harness.plugins"):
        self.package = package
        self.bus = ServiceBus()
        self._plugins: dict[str, PluginMeta] = {}

    def _full(self, name: str) -> str:
        if name.startswith(self.package):
            return name
        return f"{self.package}.{name}"

    def install(self, name: str) -> PluginMeta:
        """加载插件模块并执行 setup(bus)。重复安装返回既有实例。"""
        if name in self._plugins:
            return self._plugins[name]
        full = self._full(name)
        mod = importlib.import_module(full)
        if not hasattr(mod, "setup"):
            raise PluginError(f"插件缺少 setup(bus) 入口: {full}")
        self.bus._owner = full
        try:
            mod.setup(self.bus)
        except PluginError:
            self.bus.drop_owner(full)
            raise
        except Exception as e:  # noqa: BLE001 —— 插件失败要干净地回滚
            self.bus.drop_owner(full)
            raise PluginError(f"插件 {name} 安装失败: {type(e).__name__}: {e}") from e
        finally:
            self.bus._owner = ""
        self._plugins[name] = PluginMeta(name=name, module=mod)
        return self._plugins[name]

    def uninstall(self, name: str) -> bool:
        """执行 teardown 并回收该插件注册的全部能力/监听。"""
        meta = self._plugins.pop(name, None)
        if meta is None:
            return False
        full = self._full(name)
        teardown = getattr(meta.module, "teardown", None)
        if teardown:
            self.bus._owner = full
            try:
                teardown(self.bus)
            finally:
                self.bus._owner = ""
        self.bus.drop_owner(full)
        return True

    def names(self) -> list[str]:
        return sorted(self._plugins)

    def describe(self) -> str:
        return (f"插件({len(self._plugins)}): {', '.join(self.names())}\n"
                f"能力: {self.bus.summary()}")
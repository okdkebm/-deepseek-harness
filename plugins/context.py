# -*- coding: utf-8 -*-
"""插件：上下文管理（能力 "context"，可选）—— 卸载后循环改为发送全量历史。"""
from .. import config
from ..context import ctx_chars, trim_messages

interface = "context"


def setup(bus):
    def trim(messages):
        return trim_messages(messages, config.MAX_CTX_CHARS)

    bus.provide(interface, {"trim": trim, "chars": ctx_chars})
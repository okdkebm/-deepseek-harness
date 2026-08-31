# -*- coding: utf-8 -*-
"""插件：Mock 模型驱动（能力 "model"）—— 无模型自测，覆盖真实端点插件。"""
from ..models import MockDriver

interface = "model"


def setup(bus):
    bus.provide(interface, MockDriver())
# -*- coding: utf-8 -*-
"""插件：安全守卫（能力 "guard"）。"""
from .. import config
from ..guard import Guard as _Guard

interface = "guard"


def setup(bus):
    bus.provide(interface, _Guard(config.AUTHZ, config.WORKSPACE))
# -*- coding: utf-8 -*-
"""插件：模型驱动 —— 任意 OpenAI 兼容端点（能力 "model"）。"""
from .. import config
from ..models import ChatModel

interface = "model"


def setup(bus):
    bus.provide(interface, ChatModel(
        base_url=config.BASE_URL, model=config.MODEL, api_key=config.API_KEY,
        fallbacks=config.FALLBACK_MODELS))
# -*- coding: utf-8 -*-
"""插件：会话日志（能力 "session"）—— 造会话工厂，供 loop/cli/spawn 消费。"""
from ..config import SESSION_DIR
from ..session import Session, list_sessions

interface = "session"


def setup(bus):
    def create():
        return Session.create(SESSION_DIR)

    def resume(sid):
        return Session.resume(sid, SESSION_DIR)

    def fork(parent: Session):
        return parent.fork(SESSION_DIR)

    def lst():
        return [Session.resume(p.stem, SESSION_DIR).summary()
                for p in list_sessions(SESSION_DIR)]

    bus.provide(interface, {
        "dir": SESSION_DIR, "create": create, "resume": resume,
        "fork": fork, "list": lst,
    })
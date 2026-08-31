# -*- coding: utf-8 -*-
"""插件：ACP 服务（能力 "acp"）—— JSON-RPC 2.0 over TCP (NDJSON，每行一个对象)。

这是"万物可插件"走向服务化的入口：任何客户端（Web UI / 其他进程 / 语言）都能
远程驱动同一套总线——建会话、跑任务、装卸插件、收事件。

协议：
  请求    {"jsonrpc": "2.0", "id": 1, "method": "task.run", "params": {...}}
  响应    {"jsonrpc": "2.0", "id": 1, "result": ...}  或 {"error": {...}}
  通知    {"jsonrpc": "2.0", "method": "task.done", "params": {...}}  (服务端主动推，无 id)

方法（method + params）：
  ping                                  -> "pong"
  system.info                           -> 版本/模型/工作区/循环模式
  plugins.list                          -> {插件名: [提供的能力,...]}
  plugins.enable {"name"} / disable {"name"}
  session.create                        -> {session_id}
  session.resume {"session_id"}         -> {ok}
  session.fork  {"session_id"}          -> {session_id}
  sessions.list                         -> [{id, events, first_task},...]
  task.run {"task", "session_id"?:=""}  -> {accepted, session_id}  异步，完成广播 task.done
"""
import json
import socket
import socketserver
import threading

interface = "acp"

# ---- 错误码（JSON-RPC 2.0 约定 + 业务）----
E_PARSE = -32700
E_INVALID_REQ = -32600
E_METHOD = -32601
E_PARAMS = -32602

DEFAULT_PORT = 5213
DEFAULT_HOST = "127.0.0.1"


def setup(bus):
    """提供 ACP 服务：serve(bus, host, port) 启动 TCP JSON-RPC，供远程客户端驱动总线。"""
    bus.provide(interface, {"serve": serve})


class RpcError(Exception):
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code


def _encode(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8") + b"\n"


class _AcpHandler(socketserver.StreamRequestHandler):
    """每个连接一个线程；读逐行 JSON，方法分发，事件实时推送。"""

    def setup(self):
        super().setup()
        self.bus = self.server.bus
        self.loop_api = self.server.loop_api
        self.session_api = self.server.session_api
        self.system = self.server.system

    def _reply(self, obj) -> None:
        try:
            self.wfile.write(_encode(obj))
            self.wfile.flush()
        except OSError:
            pass

    def _notify_task_done(self, **payload) -> None:
        """bus 事件 -> 给连接推送 task.done 通知。"""
        self._reply({"jsonrpc": "2.0", "method": "task.done", "params": payload})

    def handle(self) -> None:
        self.bus.on("task.done", self._notify_task_done)
        try:
            while True:
                line = self.rfile.readline()
                if not line:
                    break
                self._handle_line(line)
        except Exception:  # noqa: BLE001 —— 连接级错误可直接断开
            pass
        finally:
            self.bus.off("task.done", self._notify_task_done)

    def _handle_line(self, line: bytes) -> None:
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            self._reply({"jsonrpc": "2.0", "id": None,
                         "error": {"code": E_PARSE, "message": "请求不是合法 JSON"}})
            return
        if req.get("jsonrpc") != "2.0" or not isinstance(req.get("method"), str):
            self._reply({"jsonrpc": "2.0", "id": req.get("id"),
                         "error": {"code": E_INVALID_REQ, "message": "非法 JSON-RPC 请求"}})
            return
        rpc_id = req.get("id")
        try:
            result = self._dispatch(req["method"], req.get("params") or {})
        except RpcError as e:
            self._reply({"jsonrpc": "2.0", "id": rpc_id,
                         "error": {"code": e.code, "message": str(e)}})
            return
        except Exception as e:  # noqa: BLE001
            self._reply({"jsonrpc": "2.0", "id": rpc_id,
                         "error": {"code": -32000, "message": f"{type(e).__name__}: {e}"}})
            return
        if rpc_id is not None:              # 带 id 才需响应（请求 vs 通知）
            self._reply({"jsonrpc": "2.0", "id": rpc_id, "result": result})

    # ---- 方法表 ----
    def _dispatch(self, method: str, params: dict):
        if method == "ping":
            return "pong"
        if method == "system.info":
            return {"mode": self.loop_api["mode"], "system": self.system}
        if method == "plugins.list":
            return self.bus.inventory()
        if method == "plugins.enable":
            host = self.bus.host
            if host is None or not host.install(params.get("name", "")):
                raise RpcError(-32000, "无法启用插件")
            return {"enabled": True, "inventory": self.bus.inventory()}
        if method == "plugins.disable":
            host = self.bus.host
            if host is None or not host.uninstall(params.get("name", "")):
                raise RpcError(-32000, "无法禁用插件")
            return {"disabled": True, "inventory": self.bus.inventory()}
        if method == "session.create":
            return {"session_id": self.session_api["create"]().id}
        if method == "session.resume":
            self.session_api["resume"](params.get("session_id", ""))
            return {"ok": True}
        if method == "session.fork":
            parent = self.session_api["resume"](params.get("session_id", ""))
            return {"session_id": self.session_api["fork"](parent).id}
        if method == "sessions.list":
            return [s for s in (self.session_api["list"]() or [])]
        if method == "task.run":
            return self._task_run(params)
        raise RpcError(E_METHOD, f"未知方法: {method}")

    def _task_run(self, params: dict) -> dict:
        task = (params.get("task") or "").strip()
        if not task:
            raise RpcError(E_PARAMS, "缺少 task")
        sid = params.get("session_id") or ""
        session = self.session_api["resume"](sid) if sid else None
        loop, session = self.loop_api["create"](self.system, session=session)
        target = session.id if session is not None else None

        def work():
            try:
                result = loop.run(task)
                self.bus.emit("task.done", session_id=target, ok=True, result=result)
            except Exception as e:  # noqa: BLE001
                self.bus.emit("task.done", session_id=target, ok=False,
                              result=f"{type(e).__name__}: {e}")

        threading.Thread(target=work, daemon=True, name="acp-task").start()
        return {"accepted": True, "session_id": target}


# ==================== 服务端启动 ====================

class _AcpServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def serve(bus, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> int:
    """启动 ACP 服务并阻塞（Ctrl+C 停止）。"""
    loop_api = bus.require("loop")
    session_api = bus.require("session")

    server = _AcpServer((host, port), _AcpHandler)
    server.bus = bus
    server.loop_api = loop_api
    server.session_api = session_api
    from .. import config
    server.system = config.DEFAULT_SYSTEM.format(workspace=config.WORKSPACE)

    print(f"[ACP] 监听 {host}:{port}  (JSON-RPC 2.0 / NDJSON)")
    print(f"[ACP] 能力: {', '.join(sorted(bus.interface_names()))}")
    try:
        with server:
            server.serve_forever()
    except KeyboardInterrupt:
        print("\n[ACP] 已停止")
    return 0


# ==================== 客户端（零依赖，供测试与集成） ====================

class AcpClient:
    """极简 TCP JSON-RPC 客户端：call 阻塞等响应，通知自动收集。"""

    def __init__(self, host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                 timeout: float = 30.0):
        self.sock = socket.create_connection((host, port), timeout=timeout)
        self.sock.settimeout(timeout)
        self._buf = b""
        self._notifications = []

    def call(self, method: str, params: dict | None = None,
             timeout: float = 60.0):
        rpc_id = int(threading.get_ident())
        payload = {"jsonrpc": "2.0", "id": rpc_id, "method": method}
        if params:
            payload["params"] = params
        self.sock.settimeout(timeout)
        self.sock.sendall(_encode(payload))
        while True:
            resp = self._read_line()
            if resp is None:
                raise TimeoutError("等待响应超时")
            if resp.get("id") == rpc_id:
                if "error" in resp:
                    e = resp["error"]
                    raise RpcError(e.get("code", -32000), e.get("message", ""))
                return resp.get("result")
            self._notifications.append(resp)   # 顺手收集服务端通知

    def drain_notifications(self) -> list:
        """取出已收到的通知（task.done 等）。"""
        out, self._notifications = self._notifications, []
        return out

    def wait_notification(self, method: str, timeout: float = 120.0):
        """阻塞等待特定方法的通知（测试用）。"""
        self.sock.settimeout(timeout)
        for n in list(self._notifications):
            if n.get("method") == method:
                self._notifications.remove(n)
                return n.get("params")
        while True:
            n = self._read_line()
            if n is None:
                raise TimeoutError(f"等待通知 {method} 超时")
            if n.get("method") == method:
                return n.get("params")
            self._notifications.append(n)

    def _read_line(self):
        while b"\n" not in self._buf:
            chunk = self.sock.recv(65536)
            if not chunk:
                return None
            self._buf += chunk
        line, self._buf = self._buf.split(b"\n", 1)
        return json.loads(line)

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass
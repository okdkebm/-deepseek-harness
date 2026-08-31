# -*- coding: utf-8 -*-
"""模型适配层：所有 LLM 走统一 OpenAI Chat Completions 协议。
换模型 = 换 BASE_URL/MODEL（config），这就是 dsh "40+ 提供商可换" 的落点。
MockDriver 用于无模型自测 harness 全链路。"""
import json
import time
import urllib.request
import urllib.error

DEFAULT_TIMEOUT = 180  # 推理超时（秒）
RETRY_HTTP_CODES = {429, 500, 502, 503, 504}  # 可重试（限流/暂时不可用）
RETRY_SLEEPS = (10, 20, 40, 60)              # 指数退避（秒）


class ModelError(Exception):
    """模型调用失败（网络/协议/额度）"""

    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def _norm_message(msg: dict) -> dict:
    """把端点原始 message 规范化为 {role, content, tool_calls} 事件存话。

    tool_calls 项规范为 {id, name, arguments(dict)}。
    """
    out = {"role": msg.get("role", "assistant"),
           "content": msg.get("content")}
    raw_calls = msg.get("tool_calls") or []
    calls = []
    for c in raw_calls:
        fn = c.get("function", {})
        try:
            args = json.loads(fn.get("arguments") or "{}")
        except json.JSONDecodeError:
            args = {}
        calls.append({"id": c.get("id") or f"call_{int(time.time()*1000)}",
                      "name": fn.get("name", ""),
                      "arguments": args})
    if calls:
        out["tool_calls"] = calls
    return out


def _post_json(url: str, payload: dict, api_key: str) -> dict:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = urllib.request.Request(url, method="POST",
                                 data=json.dumps(payload).encode("utf-8"),
                                 headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")[:300]
        raise ModelError(f"HTTP {e.code}: {e.reason} {body}", status=e.code) from e
    except urllib.error.URLError as e:
        raise ModelError(f"无法连接端点 {url}: {e.reason}") from e


class ChatModel:
    """OpenAI 兼容驱动（Ollama / OpenRouter / 任意 openai 兼容网关）。"""

    def __init__(self, base_url: str, model: str, api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key

    def name(self) -> str:
        return self.model

    def chat(self, messages: list, tools: list, temperature: float = 0.3) -> dict:
        """messages: 已裁剪的对话；tools: 工具 JSON Schema 描述。
        返回规范化 message，可能带 tool_calls。
        对 429/5xx 自动退避重试（限流时无需人工干预）。"""
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
            "temperature": temperature,
        }
        last_err: ModelError | None = None
        for attempt in range(len(RETRY_SLEEPS) + 1):
            try:
                data = _post_json(f"{self.base_url}/chat/completions", payload, self.api_key)
                try:
                    msg = data["choices"][0]["message"]
                except (KeyError, IndexError) as e:
                    raise ModelError(f"端点响应异常: {str(data)[:300]}") from e
                return _norm_message(msg)
            except ModelError as e:
                last_err = e
                if e.status not in RETRY_HTTP_CODES or attempt >= len(RETRY_SLEEPS):
                    raise
                delay = RETRY_SLEEPS[attempt]
                print(f"[重试] {self.model} 限流/暂时不可用（HTTP {e.status}），"
                      f"{delay} 秒后自动重试…", flush=True)
                time.sleep(delay)
        raise last_err


class MockDriver:
    """无模型自测驱动：固定脚本演示 多工具并行调用 -> 结果回填 -> 正常收尾。
    用于验证 循环/管道/守卫/会话 全链路（--mock）。"""

    def __init__(self):
        self._step = 0
        self.model = "mock-driver"

    def name(self) -> str:
        return self.model

    def chat(self, messages: list, tools: list, temperature: float = 0.3) -> dict:
        self._step += 1
        target = "harness/__init__.py"
        if self._step == 1:
            return _norm_message({
                "role": "assistant", "content": None,
                "tool_calls": [
                    {"id": "m1", "function": {"name": "read_file",
                        "arguments": json.dumps({"path": target})}},
                    {"id": "m2", "function": {"name": "run_command",
                        "arguments": json.dumps({"cmd": "echo mock-ok"})}},
                ],
            })
        n = sum(1 for m in messages if m.get("role") == "tool")
        return _norm_message({
            "role": "assistant",
            "content": f"（mock 完成）已读取 {target} 并执行命令，收到 {n} 个工具结果。",
        })
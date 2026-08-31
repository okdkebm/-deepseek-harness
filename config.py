# -*- coding: utf-8 -*-
"""全局配置：全部可通过环境变量覆盖。默认零成本：本地 Ollama 端点。"""
import os
import pathlib

# ---- 模型适配层配置 ----
# 本地:  http://localhost:11434/v1   （Ollama，免费）
# 云端:  https://openrouter.ai/api/v1 （免费 :free 模型，需 LLM_API_KEY）
BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
MODEL = os.environ.get("LLM_MODEL", "qwen2.5-coder:7b")
API_KEY = os.environ.get("LLM_API_KEY", "")
# 备用免费模型（限流时自动轮换），逗号分隔
FALLBACK_MODELS = [m.strip() for m in
                   os.environ.get("DSH_FALLBACK_MODELS", "").split(",") if m.strip()]

# ---- 沙箱 / 工作区 ----
WORKSPACE = pathlib.Path(os.environ.get("DSH_WORKSPACE", os.getcwd())).resolve()

# ---- 安全守卫 ----
# allow: 写入/执行类操作直接放行 | ask: 每次询问 | deny: 一律拒绝
AUTHZ = os.environ.get("DSH_AUTHZ", "ask").strip().lower()

# ---- 执行参数 ----
MAX_STEPS = int(os.environ.get("DSH_MAX_STEPS", "10"))       # 单任务最大 step
MAX_TOOL_OUTPUT = int(os.environ.get("DSH_MAX_OUTPUT", "8000"))  # 工具结果回填上限
MAX_CTX_CHARS = int(os.environ.get("DSH_MAX_CTX", "20000"))  # 发给模型的上下文上限
CMD_TIMEOUT = int(os.environ.get("DSH_CMD_TIMEOUT", "60"))   # 命令超时（秒）

# ---- 会话存储 ----
SESSION_DIR = WORKSPACE / ".dsh" / "sessions"

# ---- 系统提示词（可被 DSH_SYSTEM 覆盖）----
DEFAULT_SYSTEM = (
    "你是一个运行在用户本机沙箱中的 AI 助手（Agent Harness）。\n"
    "你有可用的工具（读文件/写文件/列目录/执行命令/派生子任务）。\n"
    "工作区根目录：{workspace}\n"
    "规则：需要动手做任务时优先调用工具；工具结果会回填给你；"
    "每次只能推进下一步，直到任务完成再总结。用简洁的中文回复。"
)
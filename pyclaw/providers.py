"""Provider catalog, model capability table and the single streaming call."""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request

# id, display, base_url, supports_temperature, thinking_mode, context_window
CATALOG = [
    ("openai", "OpenAI", "https://api.openai.com/v1", True, "openai", 400000),
    ("deepseek", "DeepSeek", "https://api.deepseek.com/v1", True, "deepseek", 1000000),
    ("mimo", "Xiaomi MiMo", "https://api.xiaomimimo.com/v1", True, "none", 256000),
    ("doubao", "豆包 / 火山方舟", "https://ark.cn-beijing.volces.com/api/v3", True, "none", 256000),
    ("kimi", "Kimi / Moonshot", "https://api.moonshot.cn/v1", False, "none", 262144),
    ("qwen", "Qwen / DashScope", "https://dashscope.aliyuncs.com/compatible-mode/v1", True, "none", 1000000),
    ("glm", "GLM / 智谱", "https://open.bigmodel.cn/api/paas/v4", True, "none", 204800),
    ("minimax", "MiniMax", "https://api.minimax.io/v1", True, "none", 204800),
    ("gemini", "Google Gemini", "https://generativelanguage.googleapis.com/v1beta/openai", True, "none", 1000000),
    ("openrouter", "OpenRouter", "https://openrouter.ai/api/v1", True, "none", 200000),
    ("siliconflow", "SiliconFlow", "https://api.siliconflow.cn/v1", True, "none", 200000),
    ("xai", "xAI", "https://api.x.ai/v1", True, "openai", 256000),
    ("mistral", "Mistral", "https://api.mistral.ai/v1", True, "none", 128000),
    ("groq", "Groq", "https://api.groq.com/openai/v1", True, "none", 128000),
    ("together", "Together AI", "https://api.together.xyz/v1", True, "none", 128000),
    ("fireworks", "Fireworks AI", "https://api.fireworks.ai/inference/v1", True, "none", 128000),
    ("cerebras", "Cerebras", "https://api.cerebras.ai/v1", True, "none", 128000),
    ("nvidia", "NVIDIA NIM", "https://integrate.api.nvidia.com/v1", True, "none", 128000),
    ("deepinfra", "DeepInfra", "https://api.deepinfra.com/v1/openai", True, "none", 128000),
    ("perplexity", "Perplexity", "https://api.perplexity.ai", True, "none", 128000),
    ("custom", "Custom", "", True, "none", 0),
]
CATALOG_BY_ID = {row[0]: row for row in CATALOG}
UNKNOWN_CONTEXT_WINDOW = 1000000

# Substring -> window. Longest match wins, so date-suffixed ids beat the family name.
MODEL_WINDOWS = [
    ("deepseek-v4-flash-0731", 1310720), ("deepseek-v4-flash", 1048576),
    ("deepseek-v4-pro", 1048576), ("deepseek-v4.1", 1048576), ("deepseek-flash", 1048576),
    ("deepseek-reasoner", 131072), ("deepseek-chat", 163840), ("deepseek-v3", 163840),
    ("kimi-k3", 1048576), ("kimi-k2", 262144), ("moonshot", 262144),
    ("glm-5.3", 1310720), ("glm-5.2", 1048576), ("glm-4.7", 204800), ("glm-4", 131072),
    ("qwen3-coder-plus", 1000000), ("qwen-plus", 1000000), ("qwen3-coder", 262144),
    ("qwen3-max", 262144), ("qwen", 131072),
    ("seed-2", 262144), ("seed-1", 262144), ("doubao", 262144),
    ("minimax-m3", 1048576), ("minimax-m2", 204800), ("minimax", 1000000),
    ("gpt-5.2-codex", 400000), ("gpt-5.1-codex", 400000), ("gpt-5-codex", 400000), ("gpt-5", 400000),
    ("claude", 200000), ("gemini", 1048576), ("grok", 256000), ("mistral", 128000),
]

# Old ids still accepted upstream but retired; used for display and context lookup only.
ALIASES = {"deepseek-v4-flash": "deepseek-flash", "deepseek-v4-flash-vision-exp": "deepseek-flash"}

DEEPSEEK_REQUEST_TIERS = ["minimal", "low", "medium", "high", "xhigh", "max", "ultra"]
DEEPSEEK_EFFORT_MAP = {"minimal": "low", "low": "low", "medium": "high", "high": "high",
                       "xhigh": "high", "max": "max", "ultra": "max"}
OPENAI_REQUEST_TIERS = ["minimal", "low", "medium", "high", "xhigh", "max", "ultra"]
OPENAI_EFFORT_MAP = {"minimal": "minimal", "low": "low", "medium": "medium", "high": "high",
                     "xhigh": "xhigh", "max": "xhigh", "ultra": "xhigh"}


def canonical_model(model):
    return ALIASES.get((model or "").strip().lower(), (model or "").strip())


def context_window(model, thinking_mode="none", configured=0, provider_id=""):
    if configured:
        return int(configured)
    name = canonical_model(model).lower()
    best = ""
    for needle, window in MODEL_WINDOWS:
        if needle in name and len(needle) > len(best):
            best, hit = needle, window
    if best:
        return hit
    row = CATALOG_BY_ID.get(provider_id)
    if row and row[5]:
        return row[5]
    return UNKNOWN_CONTEXT_WINDOW


def effort_tiers(thinking_mode):
    """Levels the request side accepts, plus their real mapping; [] hides the slider."""
    if thinking_mode == "deepseek":
        return DEEPSEEK_REQUEST_TIERS, DEEPSEEK_EFFORT_MAP
    if thinking_mode == "openai":
        return OPENAI_REQUEST_TIERS, OPENAI_EFFORT_MAP
    return [], {}


class ProviderError(Exception):
    def __init__(self, kind, message, retryable=False, overflow=False, unsupported_effort=False):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.retryable = retryable
        self.overflow = overflow
        self.unsupported_effort = unsupported_effort


_OVERFLOW_HINTS = ("context_length_exceeded", "context window", "maximum context", "too many tokens",
                   "reduce the length", "input is too long")
_EFFORT_HINTS = ("unsupported_reasoning_effort", "unsupported reasoning effort",
                 "invalid reasoning effort", "reasoning effort is not supported")


def classify(exc):
    status = getattr(exc, "status_code", None)
    text = str(getattr(exc, "message", "") or exc)
    low = text.lower()
    if status in (401, 403):
        return ProviderError("auth", text)
    if status == 429:
        return ProviderError("rate_limit", text, retryable=True)
    if status and status >= 500:
        return ProviderError("server", text, retryable=True)
    if any(h in low for h in _EFFORT_HINTS):
        return ProviderError("unsupported_effort", text, unsupported_effort=True)
    if any(h in low for h in _OVERFLOW_HINTS):
        return ProviderError("overflow", text, overflow=True)
    if status == 400:
        return ProviderError("bad_request", text)
    if status:
        return ProviderError("http", text)
    if "timeout" in low or "connection" in low or "temporarily" in low:
        return ProviderError("transport", text, retryable=True)
    return ProviderError("unknown", text)


class Provider:
    """Thin wrapper over the OpenAI SDK: one streaming call, no temperature, no max_tokens."""

    def __init__(self, cfg):
        self.reload(cfg)

    def reload(self, cfg):
        from openai import OpenAI

        self.cfg = cfg
        self.endpoint = str(cfg.get("ENDPOINT", "")).rstrip("/")
        self.model = str(cfg.get("MODEL", ""))
        self.provider_id = str(cfg.get("PROVIDER", "custom"))
        self.thinking_mode = CATALOG_BY_ID.get(self.provider_id, CATALOG_BY_ID["custom"])[4]
        try:
            configured = int(cfg.get("CONTEXT_WINDOW", 0) or 0)
        except (TypeError, ValueError):
            configured = 0
        self.context_window = context_window(self.model, self.thinking_mode, configured, self.provider_id)
        self.client = OpenAI(api_key=cfg.get("API_KEY") or "missing", base_url=self.endpoint or None,
                             max_retries=0, timeout=600.0)

    def tiers(self):
        return effort_tiers(self.thinking_mode)

    def supports_effort(self, level):
        tiers, _ = self.tiers()
        return level == "off" or level in tiers

    def _thinking_payload(self, level):
        tiers, mapping = self.tiers()
        if self.thinking_mode == "deepseek":
            if level == "off" or level not in mapping:
                return {"thinking": {"type": "disabled"}}, None
            return {"thinking": {"type": "enabled"}}, mapping[level]
        if self.thinking_mode == "openai":
            if level == "off" or level not in mapping:
                return {}, None
            return {}, mapping[level]
        return {}, None

    @staticmethod
    def prepare_messages(messages, thinking_mode):
        """DeepSeek thinking mode rejects assistant turns without reasoning_content."""
        if thinking_mode != "deepseek":
            return messages
        out = []
        for message in messages:
            if message.get("role") == "assistant" and "reasoning_content" not in message:
                message = dict(message, reasoning_content="")
            out.append(message)
        return out

    def list_models(self, timeout=20):
        if not self.endpoint:
            return []
        req = urllib.request.Request(self.endpoint + "/models",
                                     headers={"Authorization": f"Bearer {self.cfg.get('API_KEY', '')}"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8", "replace"))
        except (urllib.error.URLError, OSError, ValueError):
            return []
        items = data.get("data") if isinstance(data, dict) else None
        return [str(it.get("id")) for it in items or [] if isinstance(it, dict) and it.get("id")]

    def chat(self, messages, tools=None, effort="high", on_delta=None, signal=None):
        """One streaming call. on_delta(kind, text) sees 'text' | 'reasoning'."""
        extra, wire_effort = self._thinking_payload(effort)
        kwargs = {
            "model": self.model,
            "messages": self.prepare_messages(messages, self.thinking_mode),
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            kwargs["tools"] = tools
        if wire_effort:
            kwargs["reasoning_effort"] = wire_effort
        if extra:
            kwargs["extra_body"] = extra
        text, reasoning, usage = "", "", {}
        calls = {}
        try:
            stream = self.client.chat.completions.create(**kwargs)
        except Exception as exc:  # noqa: BLE001 - some gateways reject stream_options
            if "stream_options" not in str(exc):
                raise
            kwargs.pop("stream_options", None)
            stream = self.client.chat.completions.create(**kwargs)
        for chunk in stream:
            if signal is not None and signal.is_set():
                break
            if getattr(chunk, "usage", None):
                usage = _usage_dict(chunk.usage)
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta
            piece = getattr(delta, "content", None)
            if piece:
                text += piece
                if on_delta:
                    on_delta("delta", piece)
            thought = getattr(delta, "reasoning_content", None)
            if thought:
                reasoning += thought
                if on_delta:
                    on_delta("reasoning", thought)
            for call in getattr(delta, "tool_calls", None) or []:
                slot = calls.setdefault(getattr(call, "index", 0), {"id": "", "name": "", "arguments": ""})
                if getattr(call, "id", None):
                    slot["id"] = call.id
                fn = getattr(call, "function", None)
                if fn is not None:
                    if getattr(fn, "name", None):
                        slot["name"] = fn.name
                    if getattr(fn, "arguments", None):
                        slot["arguments"] += fn.arguments
        if not calls and not text.strip() and not reasoning.strip():
            if signal is not None and signal.is_set():
                # The user cancelled; that is not a provider failure.
                return {"content": "", "reasoning": "", "tool_calls": [], "usage": usage,
                        "cancelled": True}
            raise ProviderError("empty", "provider returned an empty response", retryable=True)
        return {"content": text, "reasoning": reasoning, "tool_calls": [calls[k] for k in sorted(calls)],
                "usage": usage}

    def chat_with_retry(self, messages, tools=None, effort="high", on_delta=None, signal=None,
                        attempts=3, sleep=time.sleep):
        last = None
        for attempt in range(attempts):
            try:
                return self.chat(messages, tools, effort, on_delta, signal)
            except ProviderError as exc:
                # A typed error may still be retryable (429, 5xx, empty response).
                # Raising it straight away meant the retry loop never ran.
                if not exc.retryable or attempt == attempts - 1:
                    raise
                last = exc
                sleep(min(8.0, 0.5 * (2 ** attempt)))
            except Exception as exc:  # noqa: BLE001 - mapped into a typed error below
                err = classify(exc)
                if not err.retryable or attempt == attempts - 1:
                    raise err from exc
                last = err
                sleep(min(8.0, 0.5 * (2 ** attempt)))
        raise last or ProviderError("unknown", "request failed")


def _usage_dict(usage):
    details = getattr(usage, "prompt_tokens_details", None)
    cached = getattr(details, "cached_tokens", None) if details else None
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
        "cache_hit_tokens": getattr(usage, "prompt_cache_hit_tokens", 0) or cached or 0,
    }


def response_error_hint(exc):
    """Readable one-liner for the transcript."""
    if isinstance(exc, ProviderError):
        return f"[{exc.kind}] {exc.message}"
    return re.sub(r"\s+", " ", str(exc))[:400]

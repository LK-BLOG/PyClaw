"""供应商目录与探测：WebUI 的 /api/providers、/api/models、/api/balance 共用一份事实来源。

设计参照 MollyPaw 的 providers/catalog.py：
- 目录在后端维护，前端只消费，不再硬编码供应商列表
- 每个供应商声明 base_url、常用模型、余额接口、Key 提示
- 网络探测统一走后端，避免浏览器跨域与密钥暴露
"""
import json
import urllib.request
import urllib.error

PROVIDERS = [
    {"id": "deepseek", "name": "DeepSeek", "base": "https://api.deepseek.com/v1",
     "root": "https://api.deepseek.com", "models": ["deepseek-chat", "deepseek-reasoner", "deepseek-v4-flash"],
     "balance": "deepseek", "key_hint": "sk-…", "docs": "https://platform.deepseek.com/api_keys"},
    {"id": "doubao", "name": "豆包 / 火山方舟", "base": "https://ark.cn-beijing.volces.com/api/v3",
     "root": "https://ark.cn-beijing.volces.com", "models": ["doubao-pro-32k", "doubao-lite-32k", "doubao-pro-128k"],
     "balance": None, "key_hint": "方舟 API Key", "docs": "https://console.volcengine.com/ark"},
    {"id": "kimi", "name": "Kimi / Moonshot", "base": "https://api.moonshot.cn/v1",
     "root": "https://api.moonshot.cn", "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
     "balance": None, "key_hint": "sk-…", "docs": "https://platform.moonshot.cn"},
    {"id": "qwen", "name": "Qwen / 通义千问", "base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
     "root": "https://dashscope.aliyuncs.com", "models": ["qwen-plus", "qwen-max", "qwen-turbo", "qwen3-max"],
     "balance": None, "key_hint": "sk-…", "docs": "https://bailian.console.aliyun.com"},
    {"id": "glm", "name": "GLM / 智谱", "base": "https://open.bigmodel.cn/api/paas/v4",
     "root": "https://open.bigmodel.cn", "models": ["glm-4-plus", "glm-4-flash", "glm-4.5"],
     "balance": None, "key_hint": "id.secret", "docs": "https://open.bigmodel.cn/usercenter/apikeys"},
    {"id": "minimax", "name": "MiniMax", "base": "https://api.minimax.io/v1",
     "root": "https://api.minimax.io", "models": ["abab6.5s-chat", "MiniMax-Text-01"],
     "balance": None, "key_hint": "eyJ…", "docs": "https://platform.minimax.io"},
    {"id": "openai", "name": "OpenAI", "base": "https://api.openai.com/v1",
     "root": "https://api.openai.com", "models": ["gpt-4o", "gpt-4o-mini", "o3-mini", "gpt-4.1"],
     "balance": None, "key_hint": "sk-…", "docs": "https://platform.openai.com/api-keys"},
    {"id": "openrouter", "name": "OpenRouter", "base": "https://openrouter.ai/api/v1",
     "root": "https://openrouter.ai", "models": ["anthropic/claude-sonnet-4", "openai/gpt-4o", "deepseek/deepseek-chat"],
     "balance": "openrouter", "key_hint": "sk-or-…", "docs": "https://openrouter.ai/keys"},
    {"id": "siliconflow", "name": "SiliconFlow", "base": "https://api.siliconflow.cn/v1",
     "root": "https://api.siliconflow.cn", "models": ["deepseek-ai/DeepSeek-V3", "Qwen/Qwen2.5-72B-Instruct"],
     "balance": None, "key_hint": "sk-…", "docs": "https://cloud.siliconflow.cn/account/ak"},
    {"id": "gemini", "name": "Google Gemini", "base": "https://generativelanguage.googleapis.com/v1beta/openai",
     "root": "https://generativelanguage.googleapis.com", "models": ["gemini-2.0-flash", "gemini-1.5-pro"],
     "balance": None, "key_hint": "AIza…", "docs": "https://aistudio.google.com/apikey"},
    {"id": "xai", "name": "xAI / Grok", "base": "https://api.x.ai/v1",
     "root": "https://api.x.ai", "models": ["grok-2-latest", "grok-beta"],
     "balance": None, "key_hint": "xai-…", "docs": "https://console.x.ai"},
    {"id": "groq", "name": "Groq", "base": "https://api.groq.com/openai/v1",
     "root": "https://api.groq.com", "models": ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
     "balance": None, "key_hint": "gsk_…", "docs": "https://console.groq.com/keys"},
    {"id": "mistral", "name": "Mistral", "base": "https://api.mistral.ai/v1",
     "root": "https://api.mistral.ai", "models": ["mistral-large-latest", "mistral-small-latest"],
     "balance": None, "key_hint": "…", "docs": "https://console.mistral.ai/api-keys"},
    {"id": "together", "name": "Together AI", "base": "https://api.together.xyz/v1",
     "root": "https://api.together.xyz", "models": ["meta-llama/Llama-3.3-70B-Instruct-Turbo"],
     "balance": None, "key_hint": "…", "docs": "https://api.together.ai/settings/api-keys"},
    {"id": "perplexity", "name": "Perplexity", "base": "https://api.perplexity.ai",
     "root": "https://api.perplexity.ai", "models": ["sonar-pro", "sonar", "sonar-reasoning"],
     "balance": None, "key_hint": "pplx-…", "docs": "https://www.perplexity.ai/settings/api"},
    {"id": "ollama", "name": "本地 Ollama", "base": "http://localhost:11434/v1",
     "root": "http://localhost:11434", "models": ["qwen2.5", "llama3.1"], "balance": None,
     "key_hint": "留空", "docs": "https://ollama.com"},
    {"id": "custom", "name": "自定义", "base": "", "root": "", "models": [], "balance": None,
     "key_hint": "任意", "docs": ""},
]

_BY_ID = {item["id"]: item for item in PROVIDERS}


def public_list():
    """给前端用的目录（去掉内部字段，保留展示所需）。"""
    out = []
    for item in PROVIDERS:
        out.append({
            "id": item["id"],
            "name": item["name"],
            "base": item["base"],
            "models": list(item["models"]),
            "balance": bool(item["balance"]),
            "key_hint": item.get("key_hint", ""),
            "docs": item.get("docs", ""),
        })
    return out


def get(provider_id):
    return _BY_ID.get(provider_id) or _BY_ID["custom"]


def _request(url, key, timeout=8):
    headers = {"User-Agent": "PyClaw", "Accept": "application/json"}
    if key:
        headers["Authorization"] = "Bearer " + key
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return json.loads(raw or b"{}")


def list_models(provider_id, key, base_override="", timeout=8):
    """后端代拉 /models；失败时回退到目录里的常用模型。"""
    item = get(provider_id)
    base = (base_override or item["base"] or "").rstrip("/")
    if not base:
        return {"ok": False, "models": item["models"], "error": "no_base"}
    url = base + "/models"
    try:
        data = _request(url, key, timeout)
    except urllib.error.HTTPError as exc:
        hint = {401: "认证失败：Key 不对或没有权限", 403: "被拒绝：Key 无权限",
                404: "该供应商没有 /models 接口"}.get(exc.code, f"HTTP {exc.code}")
        return {"ok": False, "models": item["models"], "error": hint}
    except Exception as exc:
        return {"ok": False, "models": item["models"], "error": str(exc)[:120]}
    rows = []
    payload = data.get("data") if isinstance(data, dict) else None
    if isinstance(payload, list):
        for row in payload:
            name = row.get("id") or row.get("name") if isinstance(row, dict) else None
            if name:
                rows.append(name)
    rows.sort()
    if not rows:
        return {"ok": False, "models": item["models"], "error": "返回里没有模型"}
    return {"ok": True, "models": rows[:400], "error": None}


def balance(provider_id, key, base_override=""):
    """查询余额；只对声明了 balance 的供应商有效。"""
    item = get(provider_id)
    kind = item.get("balance")
    if not kind:
        return {"ok": False, "error": "unsupported", "name": item["name"]}
    if not key:
        return {"ok": False, "error": "no_key", "name": item["name"]}
    try:
        if kind == "deepseek":
            data = _request("https://api.deepseek.com/user/balance", key)
            infos = data.get("balance_infos") or [{}]
            info = next((x for x in infos if str(x.get("currency", "")).upper() == "CNY"), None) \
                or next((x for x in infos if float(x.get("total_balance") or 0) > 0), None) \
                or infos[0]
            return {"ok": True, "name": item["name"], "currency": info.get("currency", "CNY"),
                    "total": info.get("total_balance", ""), "granted": info.get("granted_balance", ""),
                    "available": bool(data.get("is_available"))}
        if kind == "openrouter":
            data = _request("https://openrouter.ai/api/v1/credits", key)
            rows = data.get("data") or {}
            return {"ok": True, "name": item["name"], "currency": "USD",
                    "total": rows.get("total_credits", ""), "used": rows.get("total_usage", "")}
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"HTTP {exc.code}", "name": item["name"]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)[:120], "name": item["name"]}
    return {"ok": False, "error": "unsupported", "name": item["name"]}

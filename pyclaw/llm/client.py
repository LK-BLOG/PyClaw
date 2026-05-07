from abc import ABC, abstractmethod
from typing import Dict, Any
import json
import os


class LLMClient(ABC):
    """LLM客户端抽象基类 - 所有模型实现统一接口"""

    @abstractmethod
    def chat(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """
        对话接口，永远返回结构化JSON
        返回格式必须是: {"intent": "...", "params": {...}}
        """
        pass


class DeepSeekClient(LLMClient):
    """DeepSeek 官方API客户端"""

    def __init__(self, api_key: str = None, model: str = "deepseek-chat"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.model = model
        self.base_url = "https://api.deepseek.com/chat/completions"

    def chat(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        import requests

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "temperature": 0.1,  # 低温度，输出稳定
            "response_format": {"type": "json_object"},  # 强制JSON输出
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
            # 降级返回finish，不让系统炸
            return {
                "intent": "finish_task",
                "params": {"message": f"LLM调用失败: {str(e)}"}
            }


class VolcengineClient(LLMClient):
    """火山引擎Doubao API客户端"""

    def __init__(self, api_key: str = None, model: str = "ep-20241225123456-abcde"):
        self.api_key = api_key or os.getenv("VOLCENGINE_API_KEY", "")
        self.model = model
        self.base_url = f"https://ark.cn-beijing.volces.com/api/v3/chat/completions"

    def chat(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        import requests

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:
            return {
                "intent": "finish_task",
                "params": {"message": f"LLM调用失败: {str(e)}"}
            }

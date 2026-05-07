from typing import Dict, Any, Optional


class ShortTermMemory:
    """
    短期记忆 - 当前任务上下文
    生命周期：只在当前任务中存活
    """

    def __init__(self):
        self._data: Dict[str, Any] = {}

    def add(self, key: str, value: Any):
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def remove(self, key: str):
        if key in self._data:
            del self._data[key]

    def clear(self):
        self._data.clear()

    def all(self) -> Dict[str, Any]:
        return self._data.copy()

    def to_prompt_context(self) -> str:
        """转换成prompt可以用的文本格式"""
        lines = ["## 当前上下文"]
        for key, value in self._data.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

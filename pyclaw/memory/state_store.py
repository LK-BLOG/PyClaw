"""
状态存储 - USB版核心功能
负责保存和加载可迁移的系统状态
"""
import json
import os
from typing import Optional, Dict, Any


class StateStore:
    """可迁移状态存储系统"""
    STATE_FILE = "state/snapshot.json"
    TRACE_FILE = "state/trace.json"

    def __init__(self):
        self._ensure_state_dir()

    def _ensure_state_dir(self):
        """确保状态存储目录存在"""
        state_dir = os.path.dirname(self.STATE_FILE)
        if not os.path.exists(state_dir):
            os.makedirs(state_dir, exist_ok=True)

        logs_dir = "logs"
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)

    def save(self, state: Dict[str, Any]) -> None:
        """保存系统状态到 snapshot.json"""
        try:
            with open(self.STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            print(f"✅ 状态已保存到: {self.STATE_FILE}")
        except Exception as e:
            print(f"❌ 保存状态失败: {e}")

    def load(self) -> Optional[Dict[str, Any]]:
        """从 snapshot.json 加载状态"""
        try:
            if not os.path.exists(self.STATE_FILE):
                print(f"⚠️  状态文件不存在: {self.STATE_FILE}")
                return None

            with open(self.STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                print(f"✅ 状态已加载: {self.STATE_FILE}")
                return state
        except Exception as e:
            print(f"❌ 加载状态失败: {e}")
            return None

    def save_trace(self, trace: Dict[str, Any]) -> None:
        """保存执行链记录"""
        try:
            with open(self.TRACE_FILE, "w", encoding="utf-8") as f:
                json.dump(trace, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存执行链记录失败: {e}")

    def load_trace(self) -> Optional[Dict[str, Any]]:
        """加载执行链记录"""
        try:
            if not os.path.exists(self.TRACE_FILE):
                return None

            with open(self.TRACE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载执行链记录失败: {e}")
            return None

    def clear(self) -> None:
        """清除所有状态"""
        if os.path.exists(self.STATE_FILE):
            os.remove(self.STATE_FILE)
        if os.path.exists(self.TRACE_FILE):
            os.remove(self.TRACE_FILE)
        print("✅ 状态已清除")

    def export_state(self) -> Optional[Dict[str, Any]]:
        """导出可迁移的完整状态"""
        state = self.load()
        if state:
            state["export_timestamp"] = self._get_timestamp()
            return state
        return None

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d-%H%M%S")

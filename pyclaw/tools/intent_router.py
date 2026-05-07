from enum import Enum
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass

from pyclaw.policy.execution_policy import ExecutionPolicy, PolicyResult


class IntentType(Enum):
    """所有支持的意图类型"""
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    EDIT_FILE = "edit_file"
    LIST_DIR = "list_dir"
    RUN_BASH = "run_bash"
    RUN_PYTHON = "run_python"
    INSTALL_PIP = "install_pip"
    SEARCH_WEB = "search_web"
    FETCH_URL = "fetch_url"
    FINISH_TASK = "finish_task"
    ASK_USER = "ask_user"


@dataclass
class Intent:
    """结构化意图"""
    type: IntentType
    params: Dict[str, Any]

    def __repr__(self):
        return f"Intent(type={self.type.value}, params={self.params})"


class IntentRouter:
    """
    意图路由层
    作用：把LLM的输出 → 结构化Intent → 过Policy → 执行
    """

    def __init__(self):
        self.policy = ExecutionPolicy()
        self.handlers: Dict[IntentType, Callable] = {}

    def register_handler(self, intent_type: IntentType, handler: Callable):
        """注册意图处理器"""
        self.handlers[intent_type] = handler

    def parse_from_llm(self, llm_output: Dict[str, Any]) -> Intent:
        """
        从LLM的结构化输出解析意图
        LLM应该输出JSON格式：
        {
            "intent": "read_file",
            "params": {"path": "/tmp/xxx"}
        }
        """
        try:
            intent_type = IntentType(llm_output["intent"])
            params = llm_output.get("params", {})
            return Intent(type=intent_type, params=params)
        except (KeyError, ValueError) as e:
            raise ValueError(f"无法解析LLM输出: {e}") from e

    def validate(self, intent: Intent) -> PolicyResult:
        """验证意图是否符合执行策略"""
        match intent.type:
            case IntentType.READ_FILE | IntentType.LIST_DIR:
                return self.policy.check_file("read", intent.params.get("path", ""))

            case IntentType.WRITE_FILE | IntentType.EDIT_FILE:
                return self.policy.check_file("write", intent.params.get("path", ""))

            case IntentType.RUN_BASH:
                return self.policy.check_bash(intent.params.get("cmd", ""))

            case IntentType.RUN_PYTHON:
                return self.policy.check_python(intent.params.get("code", ""))

            case IntentType.INSTALL_PIP:
                return self.policy.check_pip(intent.params.get("package", ""))

            case IntentType.SEARCH_WEB | IntentType.FETCH_URL:
                from pyclaw.policy.execution_policy import RiskLevel
                return PolicyResult(allow=True, risk_level=RiskLevel.TOOL, reason="网络操作")

            case IntentType.FINISH_TASK | IntentType.ASK_USER:
                from pyclaw.policy.execution_policy import RiskLevel
                return PolicyResult(allow=True, risk_level=RiskLevel.SAFE, reason="用户交互")

            case _:
                from pyclaw.policy.execution_policy import RiskLevel
                return PolicyResult(allow=False, risk_level=RiskLevel.SYSTEM, reason=f"未知意图: {intent.type}")

    def execute(self, intent: Intent) -> Any:
        """执行意图（必须先validate）"""
        if intent.type not in self.handlers:
            raise NotImplementedError(f"没有注册处理器: {intent.type}")

        handler = self.handlers[intent.type]
        return handler(**intent.params)

    def route(self, llm_output: Dict[str, Any]) -> Dict[str, Any]:
        """完整流程：解析 → 校验 → 执行"""
        try:
            intent = self.parse_from_llm(llm_output)
            policy_result = self.validate(intent)

            if not policy_result.allow and not policy_result.require_confirm:
                return {
                    "status": "blocked",
                    "reason": policy_result.reason,
                    "risk_level": policy_result.risk_level.value
                }

            if policy_result.require_confirm:
                return {
                    "status": "require_confirm",
                    "reason": policy_result.reason,
                    "risk_level": policy_result.risk_level.value,
                    "intent": intent
                }

            result = self.execute(intent)
            return {
                "status": "success",
                "result": result,
                "risk_level": policy_result.risk_level.value
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

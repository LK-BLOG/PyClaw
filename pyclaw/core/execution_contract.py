"""
执行契约层 - 确保Planner输出与Tool输入接口一致
"""
import sys
import os
sys.path.insert(0, '/home/claw/.openclaw/workspace')

from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, ValidationError
from enum import Enum


class ActionType(str, Enum):
    """支持的动作类型枚举 - 字符串值与成员名一致"""
    write_file = "write_file"
    read_file = "read_file"
    delete_file = "delete_file"
    list_dir = "list_dir"
    run_bash = "run_bash"
    run_python = "run_python"
    finish_task = "finish_task"


class WriteFileParams(BaseModel):
    """write_file动作参数验证"""
    path: str
    content: str


class ReadFileParams(BaseModel):
    """read_file动作参数验证"""
    path: str


class DeleteFileParams(BaseModel):
    """delete_file动作参数验证"""
    path: str


class ListDirParams(BaseModel):
    """list_dir动作参数验证"""
    path: str = "./pyclaw/sandbox/workspace/"


class RunBashParams(BaseModel):
    """run_bash动作参数验证"""
    cmd: str


class RunPythonParams(BaseModel):
    """run_python动作参数验证"""
    code: str


class FinishTaskParams(BaseModel):
    """finish_task动作参数验证"""
    message: str = "任务完成"


class ExecutionContract:
    """
    执行契约验证器
    确保Planner输出与Tool输入接口一致
    """
    # 动作到参数验证模型的映射 - 使用字符串值作为键
    PARAMS_VALIDATORS = {
        ActionType.write_file: WriteFileParams,
        ActionType.read_file: ReadFileParams,
        ActionType.delete_file: DeleteFileParams,
        ActionType.list_dir: ListDirParams,
        ActionType.run_bash: RunBashParams,
        ActionType.run_python: RunPythonParams,
        ActionType.finish_task: FinishTaskParams
    }

    # 工具注册表 - 确保动作与工具匹配
    TOOL_REGISTRY = {
        ActionType.write_file: "write_file",
        ActionType.read_file: "read_file",
        ActionType.delete_file: "delete_file",
        ActionType.list_dir: "list_dir",
        ActionType.run_bash: "run_bash",
        ActionType.run_python: "run_python",
        ActionType.finish_task: "finish_task"
    }

    @classmethod
    def validate_plan(cls, plan: List[Dict[str, Any]]) -> Tuple[bool, List[Dict[str, Any]]]:
        """
        验证计划的执行契约
        返回是否有效和验证后的计划
        """
        valid_steps = []
        errors = []

        for i, step in enumerate(plan, 1):
            try:
                action = step.get("action")
                if action not in ActionType.__members__.values():
                    errors.append(f"步骤 {i}: 无效动作 '{action}'")
                    continue

                validator = cls.PARAMS_VALIDATORS[action]
                params = validator(**step.get("params", {}))

                if action in [ActionType.write_file, ActionType.read_file, ActionType.delete_file, ActionType.list_dir]:
                    path = params.path
                    if not cls._is_safe_path(path):
                        errors.append(f"步骤 {i}: 不安全的路径 '{path}'")
                        continue

                valid_step = {
                    "id": i,
                    "action": action,
                    "params": params.dict(),
                    "description": step.get("description", f"执行 {action} 动作")
                }
                valid_steps.append(valid_step)

            except ValidationError as e:
                errors.append(f"步骤 {i}: 参数验证失败 - {e}")
            except Exception as e:
                errors.append(f"步骤 {i}: 验证失败 - {e}")

        if errors:
            print("执行契约验证失败:")
            for error in errors:
                print(f"  - {error}")

        return len(errors) == 0, valid_steps

    @classmethod
    def _is_safe_path(cls, path: str) -> bool:
        """
        验证路径是否在安全沙箱内
        """
        safe_root = os.path.abspath("./pyclaw/sandbox/workspace/")
        abs_path = os.path.abspath(path)

        return abs_path.startswith(safe_root)

    @classmethod
    def validate_tool_contract(cls, step: Dict[str, Any], tool_result: Dict[str, Any]) -> bool:
        """
        验证工具执行结果与预期契约一致
        """
        action = step.get("action")

        if action == ActionType.write_file:
            path = step["params"]["path"]
            if not os.path.exists(path):
                print(f"工具契约验证失败: 文件 '{path}' 未创建")
                return False

            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if content != step["params"]["content"]:
                print(f"工具契约验证失败: 文件内容不匹配")
                print(f"  预期: '{step['params']['content']}'")
                print(f"  实际: '{content}'")
                return False

        elif action == ActionType.read_file:
            if "content" not in tool_result or not tool_result["content"]:
                print(f"工具契约验证失败: 文件内容未返回")
                return False

        elif action == ActionType.delete_file:
            path = step["params"]["path"]
            if os.path.exists(path):
                print(f"工具契约验证失败: 文件 '{path}' 未删除")
                return False

        return True

    @classmethod
    def get_contract(cls, action: str) -> Dict[str, Any]:
        """
        获取动作的契约定义
        """
        if action not in ActionType.__members__.values():
            raise ValueError(f"未知动作: '{action}'")

        validator = cls.PARAMS_VALIDATORS[action]

        import json
        return {
            "action": action,
            "params_schema": json.loads(validator.schema_json())
        }

    @classmethod
    def validate_action(cls, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证单个动作参数
        """
        if action not in ActionType.__members__.values():
            raise ValueError(f"未知动作: '{action}'")

        validator = cls.PARAMS_VALIDATORS[action]
        try:
            return validator(**params).dict()
        except ValidationError as e:
            raise ValueError(f"参数验证失败: {e}") from e


class ContractValidator:
    """
    运行时执行契约验证器
    """
    def __init__(self):
        self.contract = ExecutionContract()

    def validate_plan(self, plan: List[Dict[str, Any]]):
        valid, validated_plan = self.contract.validate_plan(plan)
        if not valid:
            raise RuntimeError("计划执行契约验证失败")
        return validated_plan

    def validate_step(self, step: Dict[str, Any], tool_result: Dict[str, Any]) -> bool:
        return self.contract.validate_tool_contract(step, tool_result)

    def validate_action(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        return ExecutionContract.validate_action(action, params)


global_contract = ContractValidator()

from typing import Dict, Any
from dataclasses import dataclass

from pyclaw.core.planner import Step


@dataclass
class Evaluation:
    ok: bool
    reason: str = ""
    need_replan: bool = False


class Evaluator:
    """
    步骤评估器 - Self-Correction的核心判断层
    负责判断这一步是否成功，是否需要重规划
    """

    MAX_REPLAN_THRESHOLD = 2  # 连续2次失败触发重规划

    def __init__(self):
        self.consecutive_failures = 0

    def check_step(self, step: Step, result: Dict[str, Any]) -> Evaluation:
        """
        评估单步执行结果
        返回是否成功，是否需要重规划
        """
        # 1. 检查Tool执行错误
        if isinstance(result, dict):
            # Tool显式error字段
            if "error" in result:
                self.consecutive_failures += 1
                return Evaluation(
                    ok=False,
                    reason=result["error"],
                    need_replan=self.consecutive_failures >= self.MAX_REPLAN_THRESHOLD
                )

            # Bash非0退出码
            if "returncode" in result and result["returncode"] != 0:
                self.consecutive_failures += 1
                return Evaluation(
                    ok=False,
                    reason=f"bash返回码 {result['returncode']}",
                    need_replan=self.consecutive_failures >= self.MAX_REPLAN_THRESHOLD
                )

        # 2. 执行成功
        self.consecutive_failures = 0
        return Evaluation(ok=True)

    def reset(self):
        """重置失败计数"""
        self.consecutive_failures = 0

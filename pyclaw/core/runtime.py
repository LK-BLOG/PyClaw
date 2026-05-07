"""
PyClaw USB版运行时 - 执行引擎
负责整个系统的调度、状态管理和任务执行
现在包含执行契约验证功能
"""
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from pyclaw.tools.intent_router import IntentRouter, Intent
from pyclaw.memory.short_term import ShortTermMemory
from pyclaw.llm.prompt_builder import PromptBuilder
from pyclaw.core.planner import Planner, Step
from pyclaw.core.evaluator import Evaluator, Evaluation
from pyclaw.core.trace import RuntimeTrace, TraceRecord
from pyclaw.core.execution_contract import global_contract, ExecutionContract


class RuntimeState(Enum):
    IDLE = "idle"
    THINKING = "thinking"
    EXECUTING = "executing"
    WAITING_CONFIRM = "waiting_confirm"
    FINISHED = "finished"
    ERROR = "error"


@dataclass
class StepResult:
    step: int
    intent: Optional[Intent]
    policy_result: Optional[Dict[str, Any]]
    tool_result: Optional[Any]
    observation: str


class AgentRuntime:
    """
    PyClaw USB v1 Runtime Core
    支持状态保存和恢复的执行引擎
    现在包含执行契约验证
    """

    def __init__(self, llm_client=None, trace: bool = False, state: Optional[Dict[str, Any]] = None):
        self.state = RuntimeState.IDLE
        self.step_count = 0
        self.max_steps = 10  # 防止无限循环
        self.max_replans = 2  # 最大重规划次数
        self.replan_count = 0

        # 核心模块
        self.intent_router = IntentRouter()
        self.short_term = ShortTermMemory()
        self.prompt_builder = PromptBuilder()
        self.llm_client = llm_client

        # 🆕 Planner - 任务拆解器
        self.planner = Planner(llm_client)
        self.current_plan: List[Step] = []
        self.plan_index: int = 0

        # 🆕 Evaluator - 评估器
        self.evaluator = Evaluator()

        # 🆕 Runtime Trace System
        self.trace_enabled = trace
        self.trace = None

        # 🆕 状态管理
        self.state_store = state or {}
        self.task_id = self.state_store.get("task_id", self._generate_task_id())
        self.export_timestamp = self.state_store.get("export_timestamp", None)

        # 待确认的意图
        self.pending_intent: Optional[Intent] = None

        # 恢复之前的状态
        if state:
            self._restore_state(state)

    def _generate_task_id(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d-%H%M%S")

    def _restore_state(self, state: Dict[str, Any]):
        if "task" in state:
            self.short_term.add("task", state["task"])

        if "current_step" in state:
            self.step_count = state["current_step"]

        if "plan" in state and state["plan"]:
            self.current_plan = []
            for step_data in state["plan"]:
                step = Step(
                    id=step_data.get("id", 0),
                    action=step_data.get("action", "finish_task"),
                    params=step_data.get("params", {}),
                    description=step_data.get("description", "")
                )
                self.current_plan.append(step)

        if "plan_index" in state:
            self.plan_index = state["plan_index"]

        if "replan_count" in state:
            self.replan_count = state["replan_count"]

        if "memory" in state and state["memory"]:
            for key, value in state["memory"].items():
                self.short_term.add(key, value)

        self.state = RuntimeState.THINKING

    def register_tool(self, tool):
        self.intent_router.register_handler(tool.intent_type, tool.execute)

    def set_task(self, task: str):
        self.state = RuntimeState.THINKING
        self.step_count = 0
        self.short_term.clear()
        self.short_term.add("task", task)
        self.pending_intent = None
        self.plan_index = 0

        if self.trace_enabled:
            self.trace = RuntimeTrace(task)
            self.trace.start()

        self.current_plan = self.planner.plan(task, self.short_term)
        print(f"📋 规划完成，共 {len(self.current_plan)} 步")
        for step in self.current_plan:
            print(f"   {step.id}. [{step.action}] {step.description}")

    def export_state(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "export_timestamp": datetime.now().strftime("%Y%m%d-%H%M%S"),
            "task": self.short_term.get("task", "Unknown"),
            "current_step": self.step_count,
            "plan": [
                {
                    "id": step.id,
                    "action": step.action,
                    "params": step.params,
                    "description": step.description
                }
                for step in self.current_plan
            ],
            "plan_index": self.plan_index,
            "replan_count": self.replan_count,
            "state": self.state.value,
            "memory": self.short_term.all(),
            "pending_intent": self.pending_intent.__dict__ if self.pending_intent else None
        }

    def step(self) -> StepResult:
        step_start_time = datetime.now()

        if self.state == RuntimeState.FINISHED:
            return StepResult(
                step=self.step_count,
                intent=None,
                policy_result=None,
                tool_result=None,
                observation="任务已完成"
            )

        if self.step_count >= self.max_steps:
            self.state = RuntimeState.FINISHED
            if self.trace_enabled:
                self.trace.record(
                    layer="runtime",
                    component="runtime",
                    action="step",
                    params={"max_steps": self.max_steps},
                    status="failure",
                    result="已达最大步数限制",
                    duration=(datetime.now() - step_start_time).total_seconds()
                )
            return StepResult(
                step=self.step_count,
                intent=None,
                policy_result=None,
                tool_result=None,
                observation="已达最大步数限制"
            )

        if self.replan_count >= self.max_replans:
            self.state = RuntimeState.FINISHED
            if self.trace_enabled:
                self.trace.record(
                    layer="runtime",
                    component="runtime",
                    action="step",
                    params={"max_replans": self.max_replans},
                    status="failure",
                    result="已达最大重规划次数，任务中止",
                    duration=(datetime.now() - step_start_time).total_seconds()
                )
            return StepResult(
                step=self.step_count,
                intent=None,
                policy_result=None,
                tool_result=None,
                observation="已达最大重规划次数，任务中止"
            )

        if self.plan_index >= len(self.current_plan):
            self.state = RuntimeState.FINISHED
            if self.trace_enabled:
                self.trace.finish()
            return StepResult(
                step=self.step_count,
                intent=None,
                policy_result=None,
                tool_result=None,
                observation="任务已完成"
            )

        self.step_count += 1
        self.state = RuntimeState.EXECUTING

        current_step = self.current_plan[self.plan_index]
        self.plan_index += 1

        if self.trace_enabled:
            self.trace.record(
                layer="planner",
                component="planner",
                action="step",
                params={
                    "step_id": current_step.id,
                    "action": current_step.action,
                    "description": current_step.description
                },
                status="success",
                result="计划步骤执行开始",
                duration=(datetime.now() - step_start_time).total_seconds()
            )

        llm_output = {
            "intent": current_step.action,
            "params": current_step.params
        }

        route_result = self.intent_router.route(llm_output)

        if route_result["status"] == "require_confirm":
            self.state = RuntimeState.WAITING_CONFIRM
            self.pending_intent = route_result["intent"]
            if self.trace_enabled:
                self.trace.record(
                    layer="policy",
                    component="execution_policy",
                    action="confirm",
                    params=route_result["intent"].params,
                    status="confirm",
                    result=route_result["reason"],
                    duration=(datetime.now() - step_start_time).total_seconds()
                )
            return StepResult(
                step=self.step_count,
                intent=self.pending_intent,
                policy_result=route_result,
                tool_result=None,
                observation=f"需要用户确认: {route_result['reason']}"
            )

        elif route_result["status"] == "blocked":
            self.state = RuntimeState.THINKING
            if self.trace_enabled:
                self.trace.record(
                    layer="policy",
                    component="execution_policy",
                    action="block",
                    params=route_result["intent"].params,
                    status="blocked",
                    result=route_result["reason"],
                    duration=(datetime.now() - step_start_time).total_seconds()
                )
            return StepResult(
                step=self.step_count,
                intent=None,
                policy_result=route_result,
                tool_result=None,
                observation=f"策略拦截: {route_result['reason']}"
            )

        elif route_result["status"] == "error":
            self.state = RuntimeState.ERROR
            if self.trace_enabled:
                self.trace.record(
                    layer="tool",
                    component="tool_router",
                    action="error",
                    params={"intent": current_step.action},
                    status="error",
                    result=route_result["error"],
                    duration=(datetime.now() - step_start_time).total_seconds()
                )
            return StepResult(
                step=self.step_count,
                intent=None,
                policy_result=None,
                tool_result=None,
                observation=f"错误: {route_result['error']}"
            )

        intent = self.intent_router.parse_from_llm(llm_output)
        tool_result = route_result["result"]

        if self.trace_enabled:
            self.trace.record(
                layer="tool",
                component=current_step.action,
                action=current_step.action,
                params=current_step.params,
                status="success",
                result=tool_result,
                duration=(datetime.now() - step_start_time).total_seconds()
            )

        evaluation = self.evaluator.check_step(current_step, tool_result)

        if self.trace_enabled:
            self.trace.record(
                layer="evaluator",
                component="evaluator",
                action="evaluate",
                params={"step": current_step.id, "action": current_step.action},
                status="success" if evaluation.ok else "failure",
                result=evaluation.reason if not evaluation.ok else "评估成功",
                duration=(datetime.now() - step_start_time).total_seconds()
            )

        self.short_term.add(f"step_{self.step_count}", {
            "intent": intent.type.value,
            "params": intent.params,
            "description": current_step.description,
            "result": tool_result,
            "evaluation": evaluation.__dict__
        })

        if self.trace_enabled:
            self.trace.record(
                layer="memory",
                component="short_term_memory",
                action="add",
                params={"key": f"step_{self.step_count}"},
                status="success",
                result="步骤执行记录已保存",
                duration=(datetime.now() - step_start_time).total_seconds()
            )

        # 🆕 执行契约验证
        if not global_contract.validate_step(current_step.__dict__, tool_result):
            print(f"⚠️  执行契约验证失败，触发重规划")
            self.replan_count += 1
            self.current_plan = self.planner.replan(
                old_steps=self.current_plan,
                failed_step=current_step,
                error="执行契约验证失败",
                memory=self.short_term
            )
            self.plan_index = 0
            return StepResult(
                step=self.step_count,
                intent=intent,
                policy_result=route_result,
                tool_result=tool_result,
                observation="执行契约验证失败，已触发重规划"
            )

        if not evaluation.ok:
            self.replan_count += 1
            print(f"🔄 第 {self.replan_count} 次重规划...")
            self.current_plan = self.planner.replan(
                old_steps=self.current_plan,
                failed_step=current_step,
                error=evaluation.reason,
                memory=self.short_term
            )
            self.plan_index = 0
            if self.trace_enabled:
                self.trace.record(
                    layer="planner",
                    component="self_correction_planner",
                    action="replan",
                    params={"replan_count": self.replan_count, "failed_step": current_step.id},
                    status="failure",
                    result=f"重规划，失败原因: {evaluation.reason}",
                    duration=(datetime.now() - step_start_time).total_seconds()
                )
            return StepResult(
                step=self.step_count,
                intent=intent,
                policy_result=route_result,
                tool_result=tool_result,
                observation=f"❌ 失败: {evaluation.reason}，已触发重规划"
            )

        if intent.type.value == "finish_task":
            self.state = RuntimeState.FINISHED
            if self.trace_enabled:
                self.trace.finish()

        return StepResult(
            step=self.step_count,
            intent=intent,
            policy_result=route_result,
            tool_result=tool_result,
            observation=f"✅ 成功: {current_step.description}"
        )

    def confirm(self, yes: bool):
        if not self.pending_intent:
            return

        if yes:
            result = self.intent_router.execute(self.pending_intent)
            self.pending_intent = None
            self.state = RuntimeState.THINKING
            return result
        else:
            self.pending_intent = None
            self.state = RuntimeState.THINKING
            return None

    def run_until_complete(self):
        results = []
        while self.state not in [RuntimeState.FINISHED, RuntimeState.WAITING_CONFIRM, RuntimeState.ERROR]:
            result = self.step()
            results.append(result)
            if self.state == RuntimeState.WAITING_CONFIRM:
                break
        return results

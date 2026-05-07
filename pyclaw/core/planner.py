from typing import List, Dict, Any
from dataclasses import dataclass
from pyclaw.llm.client import LLMClient
from pyclaw.memory.short_term import ShortTermMemory
from pyclaw.core.intent_parser import IntentParser, TaskCompiler, IntentType
from pyclaw.core.execution_contract import global_contract, ExecutionContract


@dataclass
class Step:
    """单步计划 - 与Execution Contract一致"""
    id: int
    action: str
    params: Dict[str, Any]
    description: str


class Planner:
    """
    任务拆解器 - PyClaw的"左脑"
    负责把复杂任务 → 可执行的步骤列表
    确保输出符合Execution Contract
    """

    SYSTEM_PROMPT = """
You are PyClaw Planner - Task Decomposition Engine.

Your job: Break the user's task into a CLEAR, EXECUTABLE sequence of steps.

## Available Actions
- read_file(path)
- write_file(path, content)
- run_bash(cmd)
- run_python(code)
- install_pip(package)
- finish_task(message)

## CRITICAL RULES
1. Output ONLY valid JSON. No extra text, no explanation.
2. Each step MUST map exactly to one action above.
3. Maximum 5 steps per plan. Keep it simple.
4. No nested steps. No sub-plans.
5. If you don't know, use finish_task and explain why.

## Output Format
{
  "steps": [
    {
      "id": 1,
      "action": "tool_name",
      "params": {"key": "value"},
      "description": "what this step does"
    }
  ]
}
"""

    def __init__(self, llm_client: LLMClient = None):
        self.llm_client = llm_client
        self.intent_parser = IntentParser()
        self.task_compiler = TaskCompiler()

    def plan(self, task: str, memory: ShortTermMemory) -> List[Step]:
        """
        任务拆解主方法 - 确保计划符合Execution Contract
        """
        try:
            # 1. 语义解析
            intent_list = self.intent_parser.parse(task)
            print(f"🧠 识别到意图: {[intent.type.value for intent in intent_list]}")
            
            # 2. 任务编译
            compiled_steps = self.task_compiler.compile(intent_list)
            print(f"📋 编译后的步骤: {len(compiled_steps)} 个")
            
            # 3. 执行契约验证
            valid, valid_steps = ExecutionContract.validate_plan(compiled_steps)
            if not valid:
                raise RuntimeError("计划执行契约验证失败")
            
            # 4. 转换为Step对象
            steps = []
            for i, step_data in enumerate(valid_steps, 1):
                step = Step(
                    id=i,
                    action=step_data["action"],
                    params=step_data["params"],
                    description=step_data["description"]
                )
                steps.append(step)
                print(f"   步骤 {i}: [{step.action}] {step.description}")
            
            print("✅ 计划生成完成（符合执行契约）")
            return steps
            
        except Exception as e:
            print(f"❌ 计划生成失败: {e}")
            # 兜底方案 - 生成简单步骤
            return [
                Step(
                    id=1,
                    action="finish_task",
                    params={"message": "任务理解失败"},
                    description="任务理解失败"
                )
            ]

    def replan(self, old_steps: List[Step], failed_step: Step, error: str, memory: ShortTermMemory) -> List[Step]:
        """
        自我修正重规划
        """
        print(f"🔄 触发重规划，失败步骤: {failed_step.action}, 错误: {error}")
        
        # 简单重规划策略：移除失败步骤并继续
        failed_index = -1
        for i, step in enumerate(old_steps):
            if step.id == failed_step.id:
                failed_index = i
        
        new_steps = []
        if failed_index >= 0:
            new_steps = old_steps[:failed_index]
            
            # 根据失败原因尝试调整
            if "File not found" in error or "找不到" in error:
                print("📝 调整：文件未找到，可能需要创建")
                create_step = Step(
                    id=failed_index + 1,
                    action="write_file",
                    params={
                        "path": "./pyclaw/sandbox/workspace/default.txt",
                        "content": "Hello"
                    },
                    description="创建默认文件"
                )
                new_steps.append(create_step)
            
            if failed_index < len(old_steps) - 1:
                remaining_steps = old_steps[failed_index + 1:]
                for i, step in enumerate(remaining_steps, failed_index + 1):
                    new_step = Step(
                        id=i + 1,
                        action=step.action,
                        params=step.params,
                        description=step.description
                    )
                    new_steps.append(new_step)
        
        print(f"✅ 重规划完成，新计划长度: {len(new_steps)}")
        return new_steps

    def save_plan(self, steps: List[Step], filename: str = "plan.txt"):
        """保存计划到文件"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# 任务计划 ({len(steps)} 步)\n")
            for step in steps:
                f.write(f"## 步骤 {step.id}: {step.description}\n")
                f.write(f"- 动作: {step.action}\n")
                f.write(f"- 参数: {step.params}\n\n")

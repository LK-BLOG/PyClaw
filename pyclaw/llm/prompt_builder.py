from typing import Tuple
from pyclaw.memory.short_term import ShortTermMemory


class PromptBuilder:
    """
    Prompt构建层 - 不是全量塞历史，是精选上下文
    负责把系统状态转成LLM可理解的决策输入
    """

    SYSTEM_PROMPT = """
You are PyClaw Agent - an industrial-grade AI runtime.

Your job: Decide the NEXT action to complete the user's task.

## Available Tools
- read_file(path): Read file content
- write_file(path, content): Write file
- run_bash(cmd): Execute bash command (filtered by policy)
- run_python(code): Execute Python code (sandboxed)
- install_pip(package): Install Python package (whitelist)
- finish_task(message): Mark task as complete

## Output Format
You MUST output ONLY valid JSON, no extra text:
{
  "intent": "tool_name",
  "params": {...}
}
"""

    def build(self, task: str, memory: ShortTermMemory) -> Tuple[str, str]:
        """构建system prompt + user prompt"""
        system = self.SYSTEM_PROMPT.strip()

        # 精选memory，不是全量dump
        context = self._format_context(task, memory)

        user_prompt = f"""
## Current Task
{task}

## Execution History
{context}

Decide the NEXT action. Output ONLY JSON.
"""
        return system, user_prompt.strip()

    def _format_context(self, task: str, memory: ShortTermMemory) -> str:
        """格式化上下文，做必要的压缩"""
        data = memory.all()
        lines = []

        for key, value in data.items():
            if key.startswith("step_"):
                step_num = key.split("_")[1]
                intent_type = value.get("intent", "unknown")
                # 只摘要，不贴完整result
                lines.append(f"- Step {step_num}: {intent_type}")

        if not lines:
            return "(No execution yet)"

        return "\n".join(lines)

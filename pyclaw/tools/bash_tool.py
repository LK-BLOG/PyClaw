import subprocess
from pyclaw.tools.base import BaseTool
from pyclaw.tools.intent_router import IntentType


class BashTool(BaseTool):
    name = "bash_tool"
    description = "执行bash命令（受policy保护）"
    intent_type = IntentType.RUN_BASH

    def execute(self, cmd: str, **kwargs):
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"error": "命令执行超时（30秒）"}
        except Exception as e:
            return {"error": str(e)}

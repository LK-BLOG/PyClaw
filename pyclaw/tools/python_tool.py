from pyclaw.tools.base import BaseTool
from pyclaw.tools.intent_router import IntentType


class PythonTool(BaseTool):
    name = "python_tool"
    description = "执行Python代码（受policy保护）"
    intent_type = IntentType.RUN_PYTHON

    def execute(self, code: str, **kwargs):
        try:
            # 安全沙箱：只暴露有限的builtins
            safe_builtins = {
                "print": print,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "range": range,
            }

            local_env = {}
            exec(
                code,
                {"__builtins__": safe_builtins},
                local_env
            )
            return {"result": local_env}
        except Exception as e:
            return {"error": str(e)}

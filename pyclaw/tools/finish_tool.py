from pyclaw.tools.base import BaseTool
from pyclaw.tools.intent_router import IntentType


class FinishTool(BaseTool):
    name = "finish_tool"
    description = "标记任务完成"
    intent_type = IntentType.FINISH_TASK

    def execute(self, message: str = "", **kwargs):
        return {"status": "finished", "message": message}

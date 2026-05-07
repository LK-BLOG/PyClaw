"""
写入文件的工具
专门处理WRITE_FILE意图类型
确保与Execution Contract接口一致
"""
from typing import Dict, Any
from pyclaw.tools.base import BaseTool
from pyclaw.tools.intent_router import IntentType
from pyclaw.sandbox.fs_guard import FileGuard


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "写入文件操作"
    intent_type = IntentType.WRITE_FILE

    def __init__(self):
        self.guard = FileGuard
        self.guard.ensure_workspace_exists()

    def execute(self, path: str, content: str, **kwargs) -> Dict[str, Any]:
        """
        执行写入文件操作（符合Execution Contract）
        :param path: 文件路径（相对或绝对）
        :param content: 要写入的内容
        :param kwargs: 其他参数
        :return: 操作结果（符合契约）
        """
        try:
            # 使用FileGuard验证路径
            safe_path = self.guard.safe_path(path)
            
            # 执行实际写入操作
            success = self.guard.write_text(safe_path, str(content))
            
            if success:
                # 验证写入是否成功
                if not self.guard.file_exists(safe_path):
                    return {"status": "error", "success": False, "error": "写入成功但文件不存在"}
                
                # 验证内容是否正确
                read_content = self.guard.read_text(safe_path)
                if read_content != str(content):
                    return {"status": "error", "success": False, "error": "内容不匹配"}
                
                return {
                    "status": "ok",
                    "success": True,
                    "path": safe_path,
                    "message": f"文件写入成功到 {safe_path}"
                }
            else:
                return {"status": "error", "success": False, "error": "写入操作失败"}

        except Exception as e:
            return {"status": "error", "success": False, "error": str(e)}

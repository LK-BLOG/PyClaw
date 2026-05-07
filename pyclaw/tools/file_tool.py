"""
沙箱化的文件操作工具
所有操作都通过FileGuard进行安全验证，确保只在允许的目录内操作
"""
from typing import Dict, Any
from pyclaw.tools.base import BaseTool
from pyclaw.tools.intent_router import IntentType
from pyclaw.sandbox.fs_guard import FileGuard


class FileTool(BaseTool):
    name = "file_tool"
    description = "沙箱化的文件读写操作"
    intent_type = IntentType.READ_FILE

    def __init__(self):
        self.guard = FileGuard
        self.guard.ensure_workspace_exists()

    def execute(self, path: str, content: str = None, mode: str = "read", **kwargs) -> Dict[str, Any]:
        """
        执行文件操作
        :param path: 相对或绝对路径（会被转换为安全路径）
        :param content: 写入内容（仅在write模式下需要）
        :param mode: 操作模式 read/write/append/list/delete/exists/info
        :return: 操作结果
        """
        try:
            mode = str(mode).lower()

            if mode == "read":
                return self._read_file(path)
            elif mode == "write":
                return self._write_file(path, content)
            elif mode == "append":
                return self._append_file(path, content)
            elif mode == "list":
                return self._list_dir(path)
            elif mode == "delete":
                return self._delete_file(path)
            elif mode == "exists":
                return self._file_exists(path)
            elif mode == "info":
                return self._file_info(path)
            else:
                return {"error": f"Unknown mode: {mode}"}

        except Exception as e:
            return {"error": str(e)}

    def _read_file(self, path: str) -> Dict[str, Any]:
        """读取文件"""
        try:
            content = self.guard.read_text(path)
            return {"content": content, "success": True}
        except Exception as e:
            return {"error": f"Failed to read file: {e}", "success": False}

    def _write_file(self, path: str, content: str) -> Dict[str, Any]:
        """写入文件"""
        try:
            if content is None:
                raise Exception("Content must be provided for write mode")

            success = self.guard.write_text(path, str(content))
            if success:
                return {"success": True, "message": "File written successfully"}
            else:
                return {"error": "Failed to write file", "success": False}

        except Exception as e:
            return {"error": f"Failed to write file: {e}", "success": False}

    def _append_file(self, path: str, content: str) -> Dict[str, Any]:
        """追加到文件"""
        try:
            if content is None:
                raise Exception("Content must be provided for append mode")

            success = self.guard.append_text(path, str(content))
            if success:
                return {"success": True, "message": "File appended successfully"}
            else:
                return {"error": "Failed to append file", "success": False}

        except Exception as e:
            return {"error": f"Failed to append file: {e}", "success": False}

    def _list_dir(self, path: str) -> Dict[str, Any]:
        """列出目录内容"""
        try:
            files = self.guard.list_allowed_files(path)
            file_info = []

            for file_path in files:
                info = self.guard.get_file_info(file_path)
                if info:
                    file_info.append({
                        "name": os.path.basename(file_path),
                        "path": file_path,
                        "is_dir": info.get("is_dir", False),
                        "is_file": info.get("is_file", False),
                        "size": info.get("size", 0)
                    })

            return {"content": file_info, "count": len(file_info), "success": True}

        except Exception as e:
            return {"error": f"Failed to list directory: {e}", "success": False}

    def _delete_file(self, path: str) -> Dict[str, Any]:
        """删除文件"""
        try:
            success = self.guard.remove_file(path)
            if success:
                return {"success": True, "message": "File deleted successfully"}
            else:
                return {"error": "Failed to delete file", "success": False}

        except Exception as e:
            return {"error": f"Failed to delete file: {e}", "success": False}

    def _file_exists(self, path: str) -> Dict[str, Any]:
        """检查文件是否存在"""
        try:
            exists = self.guard.file_exists(path)
            return {"exists": exists, "success": True}

        except Exception as e:
            return {"error": f"Failed to check file existence: {e}", "success": False}

    def _file_info(self, path: str) -> Dict[str, Any]:
        """获取文件信息"""
        try:
            info = self.guard.get_file_info(path)
            if info:
                return {"info": info, "success": True}
            else:
                return {"error": "File not found", "success": False}

        except Exception as e:
            return {"error": f"Failed to get file info: {e}", "success": False}

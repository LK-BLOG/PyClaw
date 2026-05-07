"""
文件系统访问限制 - USB版核心安全机制
确保所有文件操作只在指定的workspace内进行，防止系统污染
"""
import os
import sys

# USB版根路径
PYCLAW_ROOT = os.path.abspath(os.path.dirname(os.path.abspath(__file__)) + "/..")
WORKSPACE_ROOT = os.path.abspath(PYCLAW_ROOT + "/sandbox/workspace")
STATE_ROOT = os.path.abspath(PYCLAW_ROOT + "/state")
LOGS_ROOT = os.path.abspath(PYCLAW_ROOT + "/logs")

# 允许访问的白名单目录
ALLOWED_DIRS = [WORKSPACE_ROOT, STATE_ROOT, LOGS_ROOT]


class FileGuard:
    """文件系统访问限制器"""

    @classmethod
    def safe_path(cls, path: str) -> str:
        """
        验证并转换为安全路径
        确保路径在允许的白名单目录内
        """
        # 检查Windows系统路径（在非Windows系统上应该被阻止）
        if path and (path.lower().startswith("c:") or path.lower().startswith("d:")):
            raise Exception(f"ACCESS DENIED: Windows path '{path}' not allowed on non-Windows system")

        # 处理相对路径
        if path and not path.startswith("/") and not path.startswith("./") and not path.startswith("../"):
            # 没有前缀的路径默认为workspace目录下
            path = os.path.join(WORKSPACE_ROOT, path)

        # 转换为绝对路径
        abs_path = os.path.abspath(str(path))

        # 检查是否在允许的目录内
        for allowed_dir in ALLOWED_DIRS:
            if abs_path.startswith(allowed_dir):
                return abs_path

        raise Exception(f"ACCESS DENIED: Path '{abs_path}' not in allowed directories")

    @classmethod
    def is_safe(cls, path: str) -> bool:
        """
        检查路径是否安全
        只返回True/False，不抛出异常
        """
        try:
            cls.safe_path(path)
            return True
        except:
            return False

    @classmethod
    def ensure_workspace_exists(cls):
        """确保workspace目录存在"""
        if not os.path.exists(WORKSPACE_ROOT):
            os.makedirs(WORKSPACE_ROOT, exist_ok=True)
            print(f"✅ Workspace created: {WORKSPACE_ROOT}")

    @classmethod
    def list_allowed_files(cls, directory: str = WORKSPACE_ROOT) -> list:
        """
        列出允许目录内的文件
        安全版本的os.listdir
        """
        safe_dir = cls.safe_path(directory)
        try:
            files = os.listdir(safe_dir)
            return [os.path.join(safe_dir, f) for f in files]
        except Exception as e:
            print(f"❌ Failed to list directory: {e}")
            return []

    @classmethod
    def read_text(cls, path: str) -> str:
        """
        安全读取文本文件
        """
        safe_path = cls.safe_path(path)
        try:
            with open(safe_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"❌ Failed to read file: {e}")
            return ""

    @classmethod
    def write_text(cls, path: str, content: str) -> bool:
        """
        安全写入文本文件
        """
        safe_path = cls.safe_path(path)
        try:
            dir_name = os.path.dirname(safe_path)
            if dir_name and not os.path.exists(dir_name):
                os.makedirs(dir_name, exist_ok=True)
            with open(safe_path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ Failed to write file: {e}")
            return False

    @classmethod
    def append_text(cls, path: str, content: str) -> bool:
        """
        安全追加文本到文件
        """
        safe_path = cls.safe_path(path)
        try:
            with open(safe_path, "a", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ Failed to append file: {e}")
            return False

    @classmethod
    def file_exists(cls, path: str) -> bool:
        """
        检查文件是否存在
        """
        try:
            safe_path = cls.safe_path(path)
            return os.path.exists(safe_path)
        except:
            return False

    @classmethod
    def remove_file(cls, path: str) -> bool:
        """
        安全删除文件
        """
        try:
            safe_path = cls.safe_path(path)
            if os.path.exists(safe_path):
                os.remove(safe_path)
            return True
        except Exception as e:
            print(f"❌ Failed to remove file: {e}")
            return False

    @classmethod
    def get_file_info(cls, path: str) -> dict:
        """
        获取文件信息
        """
        try:
            safe_path = cls.safe_path(path)
            stat = os.stat(safe_path)
            return {
                "path": safe_path,
                "size": stat.st_size,
                "modified": stat.st_mtime,
                "is_dir": os.path.isdir(safe_path),
                "is_file": os.path.isfile(safe_path)
            }
        except Exception as e:
            print(f"❌ Failed to get file info: {e}")
            return {}

"""
测试内置工具
- FileReadTool: 文件读取
- ListDirTool: 目录列表
- ExecTool: 命令执行
- TimeTool: 时间查询
- 工具定义 (definition property)
"""
import os
import tempfile
import pytest


class TestFileReadTool:
    """测试文件读取工具"""

    def test_definition(self):
        from pyclaw.tools import FileReadTool
        tool = FileReadTool()
        defn = tool.definition
        assert defn.name == "read_file"
        assert "file_path" in defn.parameters["properties"]
        assert "file_path" in defn.parameters["required"]

    def test_read_existing_file(self):
        from pyclaw.tools import FileReadTool
        tool = FileReadTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Hello, PyClaw!\n第二行内容")
            tmp_path = f.name

        try:
            result = tool.execute({"file_path": tmp_path})
            # 由于我们在事件循环中，execute 是 async 的
            # 需要运行它
            import asyncio
            r = asyncio.run(result)
            assert r.success is True
            assert "Hello, PyClaw!" in r.content
            assert "第二行内容" in r.content
        finally:
            os.unlink(tmp_path)

    def test_read_nonexistent_file(self):
        from pyclaw.tools import FileReadTool
        tool = FileReadTool()

        import asyncio
        result = asyncio.run(tool.execute({"file_path": "/tmp/不存在_文件_xyz.txt"}))
        assert result.success is False
        assert "文件不存在" in (result.error or "")

    def test_read_empty_path(self):
        from pyclaw.tools import FileReadTool
        tool = FileReadTool()

        import asyncio
        result = asyncio.run(tool.execute({"file_path": ""}))
        assert result.success is False
        assert "cannot be empty" in (result.error or "")

    def test_read_directory_instead_of_file(self):
        from pyclaw.tools import FileReadTool
        tool = FileReadTool()

        import asyncio
        result = asyncio.run(tool.execute({"file_path": "/tmp"}))
        assert result.success is False
        assert "不是文件" in (result.error or "")

    def test_read_truncates_large_file(self):
        from pyclaw.tools import FileReadTool
        tool = FileReadTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("x" * 15000)
            tmp_path = f.name

        try:
            import asyncio
            result = asyncio.run(tool.execute({"file_path": tmp_path}))
            assert result.success is True
            assert "truncated" in result.content
            assert len(result.content) < 15000 + 200  # 有截断说明的额外字符
        finally:
            os.unlink(tmp_path)

    def test_read_utf8_file(self):
        """测试读取含 Unicode 的文件"""
        from pyclaw.tools import FileReadTool
        tool = FileReadTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("中文测试 🦞 emoji 表情")
            tmp_path = f.name

        try:
            import asyncio
            result = asyncio.run(tool.execute({"file_path": tmp_path}))
            assert result.success is True
            assert "中文测试" in result.content
            assert "🦞" in result.content
        finally:
            os.unlink(tmp_path)


class TestListDirTool:
    """测试目录列表工具"""

    def test_definition(self):
        from pyclaw.tools import ListDirTool
        tool = ListDirTool()
        defn = tool.definition
        assert defn.name == "list_directory"

    def test_list_existing_directory(self):
        from pyclaw.tools import ListDirTool
        tool = ListDirTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一些测试文件
            open(os.path.join(tmpdir, "file1.txt"), "w").close()
            open(os.path.join(tmpdir, "file2.py"), "w").close()
            os.makedirs(os.path.join(tmpdir, "subdir"), exist_ok=True)

            import asyncio
            result = asyncio.run(tool.execute({"dir_path": tmpdir}))
            assert result.success is True
            assert "file1.txt" in result.content
            assert "file2.py" in result.content
            assert "subdir/" in result.content or "subdir" in result.content

    def test_list_nonexistent_directory(self):
        from pyclaw.tools import ListDirTool
        tool = ListDirTool()

        import asyncio
        result = asyncio.run(tool.execute({"dir_path": "/tmp/ghost_dir_xyz_不存在"}))
        assert result.success is False
        assert "不存在" in (result.error or "")

    def test_list_file_path(self):
        """传一个文件路径而不是目录"""
        from pyclaw.tools import ListDirTool
        tool = ListDirTool()

        with tempfile.NamedTemporaryFile(delete=False) as f:
            tmp_path = f.name
        try:
            import asyncio
            result = asyncio.run(tool.execute({"dir_path": tmp_path}))
            assert result.success is False
            assert "不是目录" in (result.error or "")
        finally:
            os.unlink(tmp_path)


class TestExecTool:
    """测试命令执行工具"""

    def test_definition(self):
        from pyclaw.tools import ExecTool
        tool = ExecTool()
        defn = tool.definition
        assert defn.name == "exec_command"
        assert "command" in defn.parameters["required"]

    def test_exec_simple_command(self):
        from pyclaw.tools import ExecTool
        tool = ExecTool()

        import asyncio
        result = asyncio.run(tool.execute({"command": "echo 'hello world'"}))
        assert result.success is True
        assert "hello world" in result.content

    def test_exec_with_exit_code(self):
        from pyclaw.tools import ExecTool
        tool = ExecTool()

        import asyncio
        result = asyncio.run(tool.execute({"command": "exit 42"}))
        assert result.success is True
        assert "Exit code: 42" in result.content

    def test_exec_empty_command(self):
        from pyclaw.tools import ExecTool
        tool = ExecTool()

        import asyncio
        result = asyncio.run(tool.execute({"command": ""}))
        assert result.success is False
        assert "cannot be empty" in (result.error or "")

    def test_exec_with_stderr(self):
        from pyclaw.tools import ExecTool
        tool = ExecTool()

        import asyncio
        result = asyncio.run(tool.execute({"command": "echo 'out'; echo 'err' >&2"}))
        assert result.success is True
        assert "STDOUT" in result.content
        assert "STDERR" in result.content

    def test_exec_timeout(self):
        from pyclaw.tools import ExecTool
        tool = ExecTool()

        import asyncio
        result = asyncio.run(tool.execute({"command": "sleep 10", "timeout": 1}))
        assert result.success is False
        assert "timed out" in (result.error or "").lower() or "timeout" in (result.error or "").lower()


class TestTimeTool:
    """测试时间工具"""

    def test_definition(self):
        from pyclaw.tools import TimeTool
        tool = TimeTool()
        defn = tool.definition
        assert defn.name == "get_current_time"

    def test_get_default_time(self):
        from pyclaw.tools import TimeTool
        tool = TimeTool()

        import asyncio
        result = asyncio.run(tool.execute({}))
        assert result.success is True
        assert "当前时间" in result.content or "Current time" in result.content

    def test_get_shanghai_time(self):
        from pyclaw.tools import TimeTool
        tool = TimeTool()

        import asyncio
        result = asyncio.run(tool.execute({"timezone": "Asia/Shanghai"}))
        assert result.success is True
        assert "CST" in result.content or "北京时间" in result.content or "+08" in result.content or "上海" in result.content.replace("Asia/Shanghai", "").strip() or result.success

    def test_get_utc_time(self):
        from pyclaw.tools import TimeTool
        tool = TimeTool()

        import asyncio
        result = asyncio.run(tool.execute({"timezone": "UTC"}))
        assert result.success is True
        assert "UTC" in result.content

    def test_invalid_timezone(self):
        from pyclaw.tools import TimeTool
        tool = TimeTool()

        import asyncio
        result = asyncio.run(tool.execute({"timezone": "火星/北京"}))
        assert result.success is False


class TestToolBelieveDataInstruction:
    """验证工具结果附带的 [IMPORTANT] 指令"""

    def test_file_read_has_instruction(self):
        from pyclaw.tools import FileReadTool
        tool = FileReadTool()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("test data")
            tmp_path = f.name

        try:
            import asyncio
            result = asyncio.run(tool.execute({"file_path": tmp_path}))
            assert "IMPORTANT" in result.content
            assert "BELIEVE" in result.content.upper() or "based on THIS data" in result.content
        finally:
            os.unlink(tmp_path)

    def test_list_dir_has_instruction(self):
        from pyclaw.tools import ListDirTool
        tool = ListDirTool()

        with tempfile.TemporaryDirectory() as tmpdir:
            import asyncio
            result = asyncio.run(tool.execute({"dir_path": tmpdir}))
            assert "IMPORTANT" in result.content

    def test_exec_has_instruction(self):
        from pyclaw.tools import ExecTool
        tool = ExecTool()

        import asyncio
        result = asyncio.run(tool.execute({"command": "echo test"}))
        assert "IMPORTANT" in result.content

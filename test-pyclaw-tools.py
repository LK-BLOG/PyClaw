#!/usr/bin/env python3
"""PyClaw 工具调用测试脚本"""
import asyncio
import sys

sys.path.insert(0, '/home/claw/.openclaw/workspace/pyclaw-public')

from pyclaw.tools import FileReadTool, ListDirTool, ExecTool, TimeTool

async def test_tools():
    print("=" * 50)
    print("🧪 PyClaw 工具调用系统测试")
    print("=" * 50)
    
    # 测试 1: TimeTool
    print("\n1️⃣ 测试 TimeTool - 获取当前时间")
    time_tool = TimeTool()
    result = await time_tool.execute({"timezone": "Asia/Shanghai"})
    if result.success:
        print(f"✅ 成功: {result.content}")
    else:
        print(f"❌ 失败: {result.error}")
    
    # 测试 2: ListDirTool
    print("\n2️⃣ 测试 ListDirTool - 列出目录")
    list_tool = ListDirTool()
    result = await list_tool.execute({"dir_path": "/home/claw/.openclaw/workspace/pyclaw-public"})
    if result.success:
        lines = result.content.split('\n')
        print(f"✅ 成功，共 {len(lines)} 行输出")
        print(f"   预览: {lines[0]}")
    else:
        print(f"❌ 失败: {result.error}")
    
    # 测试 3: FileReadTool
    print("\n3️⃣ 测试 FileReadTool - 读取文件")
    read_tool = FileReadTool()
    result = await read_tool.execute({"file_path": "/home/claw/.openclaw/workspace/pyclaw-public/README.md"})
    if result.success:
        print(f"✅ 成功，文件大小: {len(result.content)} 字符")
    else:
        print(f"❌ 失败: {result.error}")
    
    # 测试 4: ExecTool
    print("\n4️⃣ 测试 ExecTool - 执行命令")
    exec_tool = ExecTool()
    result = await exec_tool.execute({"command": "echo 'Hello from PyClaw ExecTool!' && python3 --version"})
    if result.success:
        print(f"✅ 成功!")
        print(f"   输出: {result.content}")
    else:
        print(f"❌ 失败: {result.error}")
    
    print("\n" + "=" * 50)
    print("🏁 PyClaw 工具调用测试完成!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_tools())

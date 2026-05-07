#!/usr/bin/env python3
"""
测试任务解析过程
"""
import sys
import os
sys.path.insert(0, '/home/claw/.openclaw/workspace')

from pyclaw.core.planner import Planner
from pyclaw.sandbox.fs_guard import FileGuard
from pyclaw.memory.short_term import ShortTermMemory


def test_task_parsing():
    """测试任务解析"""
    print("🧪 测试任务解析")
    
    # 创建任务
    test_task = "创建一个临时测试文件，内容是'Clean run test'"
    
    # 测试任务解析
    planner = Planner(None)
    memory = ShortTermMemory()
    
    print(f"原始任务: {test_task}")
    
    # 测试规则匹配
    from pyclaw.core.planner import Step
    
    # 创建一个简单的memory对象
    temp_memory = type('MockMemory', (object,), {'all': lambda self: []})()
    
    # 手动测试解析
    task_lower = test_task.lower()
    print(f"是否包含创建: {'创建' in task_lower}")
    print(f"是否包含内容: {'内容' in task_lower}")
    
    import re
    file_name_match = re.search(r"名为([\u4e00-\u9fa5a-zA-Z0-9.]+)的", task_lower)
    file_content_match = re.search(r"内容是['\"](.*?)['\"]", test_task)
    
    print(f"文件名匹配: {file_name_match}")
    if file_name_match:
        print(f"文件名: {file_name_match.group(1)}")
    
    print(f"内容匹配: {file_content_match}")
    if file_content_match:
        print(f"内容: {file_content_match.group(1)}")
    
    if file_name_match:
        file_name = file_name_match.group(1)
    else:
        file_name = "test.txt"
    
    if file_content_match:
        file_content = file_content_match.group(1)
    else:
        file_content = "Hello, World!"
    
    print(f"\n最终解析结果:")
    print(f"  文件名: {file_name}")
    print(f"  内容: {file_content}")
    
    # 测试实际文件操作
    print(f"\n🧪 测试文件操作")
    
    # 创建文件
    success = FileGuard.write_text(file_name, file_content)
    print(f"创建文件: {'✅' if success else '❌'}")
    
    # 验证文件
    if FileGuard.file_exists(file_name):
        print(f"文件存在: ✅")
        
        content = FileGuard.read_text(file_name)
        print(f"文件内容: '{content}'")
        print(f"内容匹配: {'✅' if content == file_content else '❌'}")
        
        # 读取文件信息
        info = FileGuard.get_file_info(file_name)
        print(f"文件大小: {info['size']} bytes")
    else:
        print(f"文件存在: ❌")
    
    # 清理
    if FileGuard.file_exists(file_name):
        FileGuard.remove_file(file_name)
        print(f"删除文件: ✅")
    
    print(f"\n🎯 任务解析测试完成")
    
    return True


def main():
    test_task_parsing()


if __name__ == "__main__":
    main()

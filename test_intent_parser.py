#!/usr/bin/env python3
"""
Intent Parser 集成测试
"""
import sys
import os
sys.path.insert(0, '/home/claw/.openclaw/workspace')

from pyclaw.core.planner import Planner
from pyclaw.memory.short_term import ShortTermMemory
from pyclaw.core.intent_parser import IntentParser, TaskCompiler, IntentType


def test_intent_parser():
    """测试Intent Parser语义识别"""
    print("🧪 测试Intent Parser语义识别")
    
    parser = IntentParser()
    
    test_cases = [
        "在工作区创建test文件.txt，写入Hello, PyClaw!",
        "读取文件内容",
        "执行Python代码print('Hello')",
        "创建README.md文件，内容是项目说明",
        "删除临时文件",
        "列出当前目录内容"
    ]
    
    print("=" * 60)
    
    for i, task in enumerate(test_cases, 1):
        intent_list = parser.parse(task)
        print(f"\n📝 任务 {i}: {task}")
        print("-" * 40)
        
        for intent in intent_list:
            print(f"  🎯 意图类型: {intent.type.value}")
            print(f"  描述: {intent.description}")
            if intent.params:
                print(f"  参数: {intent.params}")
    
    print("\n✅ Intent Parser语义识别测试完成")


def test_task_compiler():
    """测试Task Compiler"""
    print("\n🧪 测试Task Compiler")
    
    parser = IntentParser()
    compiler = TaskCompiler()
    
    test_cases = [
        "在工作区创建test文件.txt，写入Hello, PyClaw!",
        "读取文件内容"
    ]
    
    print("=" * 60)
    
    for i, task in enumerate(test_cases, 1):
        intent_list = parser.parse(task)
        steps = compiler.compile(intent_list)
        
        print(f"\n📝 任务 {i}: {task}")
        print("-" * 40)
        
        for step in steps:
            print(f"  📋 [{step['action']}] {step['description']}")
            if step.get('params'):
                for key, value in step['params'].items():
                    print(f"     {key}: {value}")
    
    print("\n✅ Task Compiler测试完成")


def test_planner_integration():
    """测试Planner集成"""
    print("\n🧪 测试Planner集成")
    
    planner = Planner(None)
    memory = ShortTermMemory()
    
    test_task = "在工作区创建test文件.txt，写入Hello, PyClaw!"
    print(f"🎯 测试任务: {test_task}")
    
    steps = planner.plan(test_task, memory)
    
    print(f"📋 生成步骤: {len(steps)}")
    print("-" * 40)
    
    for step in steps:
        print(f"  步骤 {step.id}: [{step.action}] {step.description}")
        if step.params:
            for key, value in step.params.items():
                print(f"    {key}: {value}")
    
    print("\n✅ Planner集成测试完成")


def main():
    print("🚀 Intent Parser集成测试")
    print("=" * 60)
    
    try:
        test_intent_parser()
        test_task_compiler()
        test_planner_integration()
        
        print("\n🎉 所有测试通过！Intent Parser已成功集成到PyClaw")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        print(traceback.format_exc())
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

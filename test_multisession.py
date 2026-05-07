#!/usr/bin/env python3
"""
多会话功能测试脚本

测试会话管理器的创建、获取、删除等功能，以及通过服务器接口访问多个会话的功能。
"""
import sys
import os
sys.path.insert(0, '/home/claw/.openclaw/workspace')

import requests


class MultiSessionTester:
    """多会话功能测试类"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化测试器

        参数：
            base_url: API 服务器地址
        """
        self.base_url = base_url

    def test_health_check(self):
        """测试健康检查接口"""
        print("🏥 测试健康检查接口")
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code == 200:
                print("✅ 健康检查通过")
                return True
            else:
                print(f"❌ 健康检查失败 (状态码: {response.status_code})")
                return False
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return False

    def test_version_info(self):
        """测试版本信息接口"""
        print("🔍 测试版本信息接口")
        try:
            response = requests.get(f"{self.base_url}/version")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 版本信息获取成功")
                print(f"   版本: {data.get('version')}")
                print(f"   架构: {data.get('architecture')}")
                if 'features' in data:
                    print(f"   特性: {', '.join(data.get('features'))}")
                return True
            else:
                print(f"❌ 版本信息获取失败 (状态码: {response.status_code})")
                return False
        except Exception as e:
            print(f"❌ 版本信息获取失败: {e}")
            return False

    def test_create_session(self, session_id: str = None):
        """测试创建会话接口"""
        print(f"🎯 测试创建会话接口" + (f" (会话ID: {session_id})" if session_id else ""))
        try:
            url = f"{self.base_url}/sessions"
            payload = {}
            if session_id:
                payload["session_id"] = session_id

            response = requests.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 会话创建成功 (ID: {data.get('session_id')})")
                return data.get('session_id')
            else:
                print(f"❌ 会话创建失败 (状态码: {response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"❌ 会话创建失败: {e}")
            return None

    def test_list_sessions(self):
        """测试列出所有会话接口"""
        print("📋 测试列出所有会话接口")
        try:
            response = requests.get(f"{self.base_url}/sessions")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 会话列表获取成功")
                print(f"   会话数量: {data.get('count')}")
                if data.get('count') > 0:
                    print(f"   会话ID: {', '.join(data.get('sessions'))}")
                return data.get('sessions')
            else:
                print(f"❌ 会话列表获取失败 (状态码: {response.status_code}): {response.text}")
                return []
        except Exception as e:
            print(f"❌ 会话列表获取失败: {e}")
            return []

    def test_session_health(self, session_id: str):
        """测试会话健康检查接口"""
        print(f"🏥 测试会话健康检查接口 (会话ID: {session_id})")
        try:
            response = requests.get(f"{self.base_url}/sessions/{session_id}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 会话健康检查通过")
                return True
            else:
                print(f"❌ 会话健康检查失败 (状态码: {response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"❌ 会话健康检查失败: {e}")
            return False

    def test_run_task(self, session_id: str, task: str):
        """测试任务执行接口"""
        print(f"🚀 测试任务执行接口 (会话ID: {session_id})")
        print(f"   任务: {task}")
        try:
            response = requests.post(f"{self.base_url}/sessions/{session_id}/run",
                                     json={"task": task})
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 任务执行成功")
                return True
            else:
                print(f"❌ 任务执行失败 (状态码: {response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"❌ 任务执行失败: {e}")
            return False

    def test_export_state(self, session_id: str):
        """测试状态导出接口"""
        print(f"📤 测试状态导出接口 (会话ID: {session_id})")
        try:
            response = requests.get(f"{self.base_url}/sessions/{session_id}/state/export")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 状态导出成功")
                return data.get('state')
            else:
                print(f"❌ 状态导出失败 (状态码: {response.status_code}): {response.text}")
                return None
        except Exception as e:
            print(f"❌ 状态导出失败: {e}")
            return None

    def test_import_state(self, session_id: str, state: dict):
        """测试状态导入接口"""
        print(f"📥 测试状态导入接口 (会话ID: {session_id})")
        try:
            response = requests.post(f"{self.base_url}/sessions/{session_id}/state/import",
                                     json={"state": state})
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 状态导入成功")
                return True
            else:
                print(f"❌ 状态导入失败 (状态码: {response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"❌ 状态导入失败: {e}")
            return False

    def test_delete_session(self, session_id: str):
        """测试删除会话接口"""
        print(f"🗑️  测试删除会话接口 (会话ID: {session_id})")
        try:
            response = requests.delete(f"{self.base_url}/sessions/{session_id}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 会话删除成功")
                return True
            else:
                print(f"❌ 会话删除失败 (状态码: {response.status_code}): {response.text}")
                return False
        except Exception as e:
            print(f"❌ 会话删除失败: {e}")
            return False


def run_test_suite():
    """运行完整测试套件"""
    print("=" * 60)
    print("🚀 运行多会话功能测试套件")
    print("=" * 60)

    # 初始化测试器
    tester = MultiSessionTester()

    # 测试健康检查
    if not tester.test_health_check():
        print("\n❌ 服务器健康检查失败，无法继续测试")
        return False

    # 测试版本信息
    if not tester.test_version_info():
        print("\n❌ 服务器版本信息获取失败，无法继续测试")
        return False

    # 测试创建会话
    session1 = tester.test_create_session()
    if not session1:
        return False

    # 测试列出会话
    sessions = tester.test_list_sessions()
    if not sessions:
        return False

    # 测试会话健康检查
    if not tester.test_session_health(session1):
        return False

    # 测试任务执行
    task = "创建一个名为 test1.txt 的文件，内容为 'Hello, Session 1!'"
    if not tester.test_run_task(session1, task):
        return False

    # 测试状态导出
    state1 = tester.test_export_state(session1)
    if not state1:
        return False

    # 测试创建第二个会话
    session2 = tester.test_create_session("test-session-2")
    if not session2:
        return False

    # 测试列出会话（应该有两个会话）
    sessions = tester.test_list_sessions()
    if len(sessions) < 2:
        print("❌ 会话创建数量不足")
        return False

    # 测试任务执行（第二个会话）
    task = "创建一个名为 test2.txt 的文件，内容为 'Hello, Session 2!'"
    if not tester.test_run_task(session2, task):
        return False

    # 测试状态导出（第二个会话）
    state2 = tester.test_export_state(session2)
    if not state2:
        return False

    # 测试删除会话
    if not tester.test_delete_session(session1):
        return False

    # 测试列出会话（应该只有一个会话）
    sessions = tester.test_list_sessions()
    if len(sessions) != 1:
        print("❌ 会话数量不正确")
        return False

    # 测试删除第二个会话
    if not tester.test_delete_session(session2):
        return False

    # 测试列出会话（应该是空的）
    sessions = tester.test_list_sessions()
    if len(sessions) != 0:
        print("❌ 会话没有完全删除")
        return False

    print("\n✅" * 10)
    print("🎊 所有多会话功能测试通过！")
    print("✅" * 10)

    return True


if __name__ == "__main__":
    # 运行测试
    success = run_test_suite()

    # 退出状态码
    sys.exit(0 if success else 1)

"""
测试 Agent 核心逻辑
- 构造和属性
- 系统提示词构建（仅验证结构，不调 API）
- 消息构建
- SubAgent / SubAgentManager
"""
import os
import time
import uuid
import pytest


class TestAgentInit:
    """测试 Agent 初始化"""

    def test_create_default(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="deepseek-v4-flash")
        assert agent.api_key == "sk-test"
        assert agent.model == "deepseek-v4-flash"
        assert agent.mode == "talk"
        assert agent.thinking is False
        assert agent.max_rounds == 300
        assert agent.system_prompt is not None
        assert len(agent.system_prompt) > 0

    def test_create_coding_mode(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="deepseek-v4-flash")
        agent.mode = "coding"
        assert agent.mode == "coding"
        # 切换模式会重建提示词
        assert "Coding" in agent.system_prompt

    def test_custom_base_url(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", base_url="https://custom.api.com/v1", model="custom-model")
        assert agent.base_url == "https://custom.api.com/v1"

    def test_base_url_trailing_slash_stripped(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", base_url="https://api.test.com/", model="m")
        assert agent.base_url == "https://api.test.com"

    def test_language_setting(self):
        from pyclaw.agent import Agent
        agent_en = Agent(api_key="sk-test", model="m", language="en-US")
        assert agent_en.language == "en-US"

        agent_zh = Agent(api_key="sk-test", model="m", language="zh-CN")
        assert agent_zh.language == "zh-CN"


class TestAgentProperties:
    """测试 Agent 属性"""

    def test_model_setter(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="deepseek-v4-flash")
        agent.model = "glm-4-7-251222"
        assert agent.model == "glm-4-7-251222"

    def test_thinking_setter(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="m")
        agent.thinking = True
        assert agent.thinking is True
        agent.thinking = False
        assert agent.thinking is False

    def test_reasoning_effort(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="m")
        assert agent.reasoning_effort == "high"
        agent.reasoning_effort = "max"
        assert agent.reasoning_effort == "max"

    def test_invalid_reasoning_effort(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="m")
        agent.reasoning_effort = "invalid"
        assert agent.reasoning_effort == "high"  # 无效值不生效

    def test_mode_setter_invalid(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="m")
        agent.mode = "invalid"
        assert agent.mode == "talk"  # 无效值不生效


class TestAgentReconfigure:
    """测试重新配置"""

    def test_reconfigure_api_key(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-old", model="m")
        assert agent.api_key == "sk-old"
        agent.reconfigure(api_key="sk-new")
        assert agent.api_key == "sk-new"

    def test_reconfigure_model(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="old-model")
        agent.reconfigure(model="new-model")
        assert agent.model == "new-model"

    def test_reconfigure_empty_api_key(self):
        """空 API Key 不应生效"""
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-valid", model="m")
        agent.reconfigure(api_key="")
        assert agent.api_key == "sk-valid"  # 没被改

    def test_reconfigure_mode(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="m")
        agent.reconfigure(mode="coding")
        assert agent.mode == "coding"

    def test_reconfigure_thinking(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="m")
        agent.reconfigure(thinking=True)
        assert agent.thinking is True


class TestBuildMessages:
    """测试消息构建（不调 API）"""

    def test_build_with_system_prompt(self):
        from pyclaw.agent import Agent
        from pyclaw.pyclaw_types import Message, MessageRole

        agent = Agent(api_key="sk-test", model="m")
        messages = agent._build_messages([])
        # 第一条应是 system prompt
        assert len(messages) >= 1
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == agent.system_prompt

    def test_build_user_message(self):
        from pyclaw.agent import Agent
        from pyclaw.pyclaw_types import Message, MessageRole

        agent = Agent(api_key="sk-test", model="m")
        msg = Message(
            id="msg_1", content="你好", sender="user",
            role=MessageRole.USER, timestamp=time.time(),
            channel_id="ch", session_id="sess"
        )
        messages = agent._build_messages([msg])
        assert len(messages) == 2
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "你好"

    def test_build_assistant_message(self):
        from pyclaw.agent import Agent
        from pyclaw.pyclaw_types import Message, MessageRole

        agent = Agent(api_key="sk-test", model="m")
        msg = Message(
            id="msg_2", content="我是助手", sender="assistant",
            role=MessageRole.ASSISTANT, timestamp=time.time(),
            channel_id="ch", session_id="sess"
        )
        messages = agent._build_messages([msg])
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "我是助手"

    def test_build_tool_message(self):
        from pyclaw.agent import Agent
        from pyclaw.pyclaw_types import Message, MessageRole

        agent = Agent(api_key="sk-test", model="m")
        msg = Message(
            id="msg_3", content='{"result": "ok"}', sender="tool",
            role=MessageRole.TOOL, timestamp=time.time(),
            channel_id="ch", session_id="sess",
            tool_call_id="call_abc"
        )
        messages = agent._build_messages([msg])
        assert messages[1]["role"] == "tool"
        assert messages[1]["tool_call_id"] == "call_abc"

    def test_build_assistant_with_tool_calls(self):
        from pyclaw.agent import Agent
        from pyclaw.pyclaw_types import Message, MessageRole, ToolCall

        agent = Agent(api_key="sk-test", model="m")
        tool_calls = [
            ToolCall(id="call_1", name="read_file", arguments={"file_path": "/tmp/x.txt"})
        ]
        msg = Message(
            id="msg_4", content="", sender="assistant",
            role=MessageRole.ASSISTANT, timestamp=time.time(),
            channel_id="ch", session_id="sess",
            tool_calls=tool_calls
        )
        messages = agent._build_messages([msg])
        assert messages[1]["role"] == "assistant"
        assert "tool_calls" in messages[1]
        assert len(messages[1]["tool_calls"]) == 1
        assert messages[1]["tool_calls"][0]["function"]["name"] == "read_file"

    def test_build_multiple_messages(self):
        from pyclaw.agent import Agent
        from pyclaw.pyclaw_types import Message, MessageRole

        agent = Agent(api_key="sk-test", model="m")
        msgs = [
            Message(id="m1", content="用户1", sender="user",
                    role=MessageRole.USER, timestamp=1, channel_id="ch", session_id="s"),
            Message(id="m2", content="助手1", sender="assistant",
                    role=MessageRole.ASSISTANT, timestamp=2, channel_id="ch", session_id="s"),
            Message(id="m3", content="用户2", sender="user",
                    role=MessageRole.USER, timestamp=3, channel_id="ch", session_id="s"),
        ]
        messages = agent._build_messages(msgs)
        assert len(messages) == 4  # system + 3
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
        assert messages[3]["role"] == "user"


class TestSubAgent:
    """测试子代理"""

    def test_create_subagent(self):
        from pyclaw.agent import Agent, SubAgent
        agent = Agent(api_key="sk-test", model="m")
        sub = SubAgent("TestAgent", {"read_file"}, agent)
        assert sub.name == "TestAgent"
        assert "read_file" in sub.allowed_tool_names

    def test_create_file_agent(self):
        from pyclaw.agent import Agent, SubAgent
        agent = Agent(api_key="sk-test", model="m")
        sub = SubAgent("FileAgent", {"read_file", "list_directory", "write_file"}, agent)
        assert sub.name == "FileAgent"
        assert len(sub.allowed_tool_names) == 3

    def test_create_exec_agent(self):
        from pyclaw.agent import Agent, SubAgent
        agent = Agent(api_key="sk-test", model="m")
        sub = SubAgent("ExecAgent", {"exec_command"}, agent)
        assert sub.name == "ExecAgent"
        assert "exec_command" in sub.allowed_tool_names


class TestSubAgentManager:
    """测试子代理管理器"""

    def test_create_default_manager(self):
        from pyclaw.agent import Agent, SubAgentManager
        agent = Agent(api_key="sk-test", model="m")
        mgr = SubAgentManager(agent)
        assert mgr.agent is agent
        assert mgr.sub_agents == {}

    def test_create_exec_agent(self):
        from pyclaw.agent import Agent, SubAgentManager
        agent = Agent(api_key="sk-test", model="m")
        mgr = SubAgentManager(agent)
        sub = mgr.create_exec_agent()
        assert sub.name == "ExecAgent"
        assert "exec_command" in sub.allowed_tool_names

    def test_create_file_agent(self):
        from pyclaw.agent import Agent, SubAgentManager
        agent = Agent(api_key="sk-test", model="m")
        mgr = SubAgentManager(agent)
        sub = mgr.create_file_agent()
        assert sub.name == "FileAgent"
        assert "read_file" in sub.allowed_tool_names
        assert "write_file" in sub.allowed_tool_names

    def test_create_search_agent(self):
        from pyclaw.agent import Agent, SubAgentManager
        agent = Agent(api_key="sk-test", model="m")
        mgr = SubAgentManager(agent)
        sub = mgr.create_search_agent()
        assert sub.name == "SearchAgent"
        assert "web_search" in sub.allowed_tool_names

    def test_delegate_create_on_demand(self):
        from pyclaw.agent import Agent, SubAgentManager
        agent = Agent(api_key="sk-test", model="m")
        mgr = SubAgentManager(agent)
        # 首次 delegate 会创建子代理
        import asyncio
        # 这里不会真的调 API，因为 exec agent 只有 exec_command 工具
        # 而 sub.execute() 会调 agent.chat() → 需要 API Key
        # 我们只测 manager 创建了子代理
        result = asyncio.run(mgr.delegate("exec", "echo hello"))
        # 子代理已创建
        assert "exec" in mgr.sub_agents
        # 但由于没有真实 API，结果会是错误
        assert result is not None

    def test_unknown_agent(self):
        from pyclaw.agent import Agent, SubAgentManager
        agent = Agent(api_key="sk-test", model="m")
        mgr = SubAgentManager(agent)
        import asyncio
        result = asyncio.run(mgr.delegate("unknown", "do something"))
        assert "未知" in result or "unknown" in result.lower()


class TestAgentSystemPrompt:
    """测试系统提示词构建"""

    def test_prompt_contains_identity(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="deepseek-v4-flash")
        prompt = agent.system_prompt
        assert "DeepSeek" in prompt

    def test_prompt_contains_user_info(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="m")
        prompt = agent.system_prompt
        assert "骆戡" in prompt or "小戡" in prompt

    def test_prompt_mode_switch(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="m")
        talk_prompt = agent.system_prompt
        agent.mode = "coding"
        coding_prompt = agent.system_prompt
        # 不同模式提示词应不同
        assert talk_prompt != coding_prompt
        assert "Coding" in coding_prompt

    def test_prompt_english_talk(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="m", language="en-US")
        prompt = agent.system_prompt
        assert "骆戡" in prompt  # 用户信息不翻译
        # 系统框架词应为英文
        assert "Identity" in prompt
        assert "endpoint" in prompt.lower()

    def test_prompt_contains_tools_section(self):
        from pyclaw.agent import Agent
        agent = Agent(api_key="sk-test", model="m")
        prompt = agent.system_prompt
        assert "FileRead" in prompt or "read_file" in prompt or "ReadFile" in prompt
        # 应包含工具描述
        assert "ListDir" in prompt or "list_directory" in prompt

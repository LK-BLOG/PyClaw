"""
Gateway - PyClaw 核心网关
"""
import uuid
import time
import asyncio
from typing import Dict, List, Optional
from .types import Message, Channel, Tool, MessageRole
from .session import SessionManager
from .agent import Agent
from .skill import skill_manager
from .skill_tools import ListSkillsTool, InstallSkillTool, UninstallSkillTool
from .memory_tools import AddGlobalMemoryTool, ListGlobalMemoriesTool, SearchMemoryTool, DeleteMemoryTool


class Gateway:
    """PyClaw 网关核心"""
    
    def __init__(self, llm_api_key: str, **kwargs):
        self.session_manager = SessionManager()
        self.agent = Agent(api_key=llm_api_key, **kwargs)
        self.channels: Dict[str, Channel] = {}
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # 发现 Skill（同步）
        self._discover_skills()
        self._skill_system_ready = False
    
    def _discover_skills(self):
        """发现所有 Skill（同步调用）"""
        print()
        print("=" * 50)
        print("🔌 初始化 Skill 插件系统")
        print("=" * 50)
        
        # 1. 发现并加载所有 Skill
        loaded = skill_manager.discover_skills()
        print(f"发现并加载了 {len(loaded)} 个 Skill")
    
    async def initialize_skills(self):
        """初始化 Skill 插件系统（异步调用，在事件循环中调用）"""
        if self._skill_system_ready:
            return
        
        # 2. 初始化所有 Skill
        initialized = await skill_manager.initialize_all()
        print(f"成功初始化 {initialized} 个 Skill")
        
        # 3. 注册所有 Skill 的工具
        skill_tools = skill_manager.get_all_tools()
        for tool in skill_tools:
            self.agent.register_tool(tool)
        print(f"注册了 {len(skill_tools)} 个来自 Skill 的工具")
        
        # 4. 注册 Skill 管理工具
        self.agent.register_tool(ListSkillsTool())
        self.agent.register_tool(InstallSkillTool())
        self.agent.register_tool(UninstallSkillTool())
        print("注册了 3 个 Skill 管理工具")
        
        # 5. 注册记忆管理工具
        self.agent.register_tool(AddGlobalMemoryTool())
        self.agent.register_tool(ListGlobalMemoriesTool())
        self.agent.register_tool(SearchMemoryTool())
        self.agent.register_tool(DeleteMemoryTool())
        print("注册了 4 个记忆管理工具")
        
        print("=" * 50)
        print()
        self._skill_system_ready = True
    
    def register_channel(self, channel: Channel) -> None:
        """注册消息通道"""
        self.channels[channel.id] = channel
        channel.on_message(self._handle_message)
    
    def register_tool(self, tool: Tool) -> None:
        """注册工具"""
        self.agent.register_tool(tool)
    
    async def start(self) -> None:
        """启动网关"""
        self._running = True
        print("🚀 PyClaw Gateway 启动中...")
        
        # 启动所有 channel
        for channel in self.channels.values():
            task = asyncio.create_task(channel.start())
            self._tasks.append(task)
        
        print(f"✅ 已注册 {len(self.channels)} 个通道")
        print(f"✅ 已注册 {len(self.agent.tools)} 个工具")
        print("🎯 Gateway 运行中...")
        
        # 保持运行
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            await self.stop()
    
    async def stop(self) -> None:
        """停止网关"""
        self._running = False
        
        for task in self._tasks:
            task.cancel()
        
        for channel in self.channels.values():
            await channel.stop()
        
        print("\n👋 PyClaw Gateway 已停止")
    
    async def _handle_message(self, message: Message) -> None:
        """处理收到的消息"""
        # 1. 添加消息到会话
        self.session_manager.add_message(message.session_id, message)
        
        # 2. 获取会话历史
        history = self.session_manager.get_history(message.session_id)
        
        # 3. 调用 Agent
        try:
            response = await self.agent.chat(history)
            
            # 4. 处理工具调用
            while response.tool_calls:
                for tool_call in response.tool_calls:
                    result = await self.agent.execute_tool(tool_call)
                    
                    # 添加工具结果到历史
                    tool_result_msg = Message(
                        id=f"msg_{uuid.uuid4().hex[:8]}",
                        content=result or "",
                        sender="system",
                        role=MessageRole.TOOL,
                        timestamp=time.time(),
                        channel_id=message.channel_id,
                        session_id=message.session_id,
                        tool_call_id=tool_call.id
                    )
                    self.session_manager.add_message(message.session_id, tool_result_msg)
                
                # 再次调用 LLM 获取最终回答
                history = self.session_manager.get_history(message.session_id)
                response = await self.agent.chat(history)
            
            # 5. 发送响应
            if response.content:
                channel = self.channels.get(message.channel_id)
                if channel:
                    await channel.send_message(message.session_id, response.content)
                
                # 添加助手响应到历史
                assistant_msg = Message(
                    id=f"msg_{uuid.uuid4().hex[:8]}",
                    content=response.content,
                    sender="assistant",
                    role=MessageRole.ASSISTANT,
                    timestamp=time.time(),
                    channel_id=message.channel_id,
                    session_id=message.session_id
                )
                self.session_manager.add_message(message.session_id, assistant_msg)
        
        except Exception as e:
            error_msg = f"处理消息时出错: {str(e)}"
            print(f"❌ {error_msg}")
            channel = self.channels.get(message.channel_id)
            if channel:
                await channel.send_message(message.session_id, error_msg)

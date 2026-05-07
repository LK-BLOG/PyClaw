"""
消息通道实现
"""
import uuid
import time
import asyncio
from typing import Callable, Optional
from .types import Message, MessageRole


class CLIChannel:
    """命令行交互通道"""
    
    id: str = "cli"
    name: str = "Command Line Interface"
    
    def __init__(self):
        self._callback: Optional[Callable[[Message], None]] = None
        self._session_id = f"cli_{uuid.uuid4().hex[:8]}"
    
    def on_message(self, callback: Callable[[Message], None]) -> None:
        """设置消息回调"""
        self._callback = callback
    
    async def start(self) -> None:
        """启动 CLI 通道"""
        print(f"📟 CLI Channel 已启动 (会话ID: {self._session_id})")
        print("输入消息与AI对话，输入 'quit' 退出\n")
        
        # 在后台运行输入循环
        loop = asyncio.get_event_loop()
        while True:
            try:
                user_input = await loop.run_in_executor(None, input, "你: ")
                
                if user_input.lower() in ["quit", "exit", "退出"]:
                    print("退出 CLI Channel")
                    break
                
                if not user_input.strip():
                    continue
                
                message = Message(
                    id=f"msg_{uuid.uuid4().hex[:8]}",
                    content=user_input,
                    sender="user",
                    role=MessageRole.USER,
                    timestamp=time.time(),
                    channel_id=self.id,
                    session_id=self._session_id
                )
                
                if self._callback:
                    await self._callback(message)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"CLI 错误: {e}")
                break
    
    async def stop(self) -> None:
        """停止通道"""
        pass
    
    async def send_message(self, session_id: str, content: str) -> None:
        """发送消息到 CLI"""
        print(f"\n🤖 PyClaw: {content}\n")


class WebChatChannel:
    """简单的 Web 聊天通道"""
    
    id: str = "webchat"
    name: str = "Web Chat"
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self._callback: Optional[Callable[[Message], None]] = None
        self._connections: dict[str, asyncio.Queue] = {}
    
    def on_message(self, callback: Callable[[Message], None]) -> None:
        self._callback = callback
    
    async def start(self) -> None:
        """启动 WebSocket 服务器"""
        try:
            import websockets
        except ImportError:
            print("⚠️  请安装 websockets: pip install websockets")
            return
        
        print(f"🌐 WebChat Channel 启动在 ws://{self.host}:{self.port}")
        
        async def handler(websocket):
            session_id = f"ws_{uuid.uuid4().hex[:8]}"
            self._connections[session_id] = websocket
            
            try:
                async for message in websocket:
                    msg = Message(
                        id=f"msg_{uuid.uuid4().hex[:8]}",
                        content=message,
                        sender="web_user",
                        role=MessageRole.USER,
                        timestamp=time.time(),
                        channel_id=self.id,
                        session_id=session_id
                    )
                    if self._callback:
                        await self._callback(msg)
            finally:
                del self._connections[session_id]
        
        server = await websockets.serve(handler, self.host, self.port)
        await server.wait_closed()
    
    async def stop(self) -> None:
        pass
    
    async def send_message(self, session_id: str, content: str) -> None:
        """发送消息到 WebSocket 客户端"""
        if session_id in self._connections:
            websocket = self._connections[session_id]
            try:
                await websocket.send(content)
            except Exception:
                pass

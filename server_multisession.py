#!/usr/bin/env python3
"""
PyClaw USB 后端 API 服务 - 多会话支持

提供远程访问 PyClaw 的 HTTP 接口，支持任务执行、状态导出和导入，
并新增多会话管理功能。
"""
import sys
import os
sys.path.insert(0, '/home/claw/.openclaw/workspace')

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from session_manager import get_session_manager, SessionManager
from pyclaw import create_runtime


class TaskRequest(BaseModel):
    """任务请求模型"""
    task: str
    state: Dict[str, Any] = None


class StateRequest(BaseModel):
    """状态请求模型"""
    state: Dict[str, Any]


class SessionCreateRequest(BaseModel):
    """会话创建请求模型"""
    session_id: Optional[str] = None


class SessionResponse(BaseModel):
    """会话响应模型"""
    success: bool
    session_id: str
    message: str


class SessionsListResponse(BaseModel):
    """会话列表响应模型"""
    success: bool
    sessions: List[str]
    count: int


# 创建应用
app = FastAPI(title="PyClaw USB API", version="1.1", description="支持多会话的 PyClaw USB API")

# 配置 CORS 中间件（允许所有来源，生产环境应限制）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": "2026-05-03"}


@app.get("/version")
async def get_version():
    """获取版本信息接口"""
    return {
        "success": True,
        "version": "1.1",
        "architecture": "PyClaw USB API Freeze Layer",
        "features": ["multi-session", "state-management", "task-execution"]
    }


@app.post("/sessions", response_model=SessionResponse)
async def create_session(request: SessionCreateRequest, manager: SessionManager = Depends(get_session_manager)):
    """
    创建新会话接口

    参数：
        request: 会话创建请求，包含可选的 session_id

    返回：
        会话创建结果
    """
    try:
        session_id = manager.create_session(request.session_id)
        return SessionResponse(
            success=True,
            session_id=session_id,
            message=f"会话创建成功 (ID: {session_id})"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/health")
async def check_session_health(session_id: str, manager: SessionManager = Depends(get_session_manager)):
    """
    检查会话健康状态接口

    参数：
        session_id: 会话ID

    返回：
        会话健康状态
    """
    try:
        manager.get_session(session_id)
        return {"status": "healthy", "session_id": session_id}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str, manager: SessionManager = Depends(get_session_manager)):
    """
    删除会话接口

    参数：
        session_id: 会话ID

    返回：
        删除结果
    """
    try:
        manager.delete_session(session_id)
        return {"success": True, "message": f"会话 {session_id} 已删除"}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions", response_model=SessionsListResponse)
async def list_sessions(manager: SessionManager = Depends(get_session_manager)):
    """
    列出所有会话接口

    返回：
        会话列表
    """
    try:
        sessions = manager.list_sessions()
        return SessionsListResponse(
            success=True,
            sessions=sessions,
            count=manager.get_session_count()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/run")
async def run_task(session_id: str, task_req: TaskRequest, manager: SessionManager = Depends(get_session_manager)):
    """
    执行任务接口 - 会话级别

    参数：
        session_id: 会话ID
        task_req: 任务请求，包含任务描述和可选状态

    返回：
        任务执行结果
    """
    try:
        runtime = manager.get_session(session_id)

        # 如果提供了状态，先导入
        if task_req.state:
            runtime.import_state(task_req.state)

        # 执行任务
        result = runtime.run(task_req.task)

        return {
            "success": True,
            "session_id": session_id,
            "task": task_req.task,
            "result": str(result)
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/state/export")
async def export_state(session_id: str, manager: SessionManager = Depends(get_session_manager)):
    """
    导出状态接口 - 会话级别

    参数：
        session_id: 会话ID

    返回：
        导出的状态数据
    """
    try:
        runtime = manager.get_session(session_id)
        state = runtime.export_state()
        return {"success": True, "session_id": session_id, "state": state}
    except KeyError:
        raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sessions/{session_id}/state/import")
async def import_state(session_id: str, state_req: StateRequest, manager: SessionManager = Depends(get_session_manager)):
    """
    导入状态接口 - 会话级别

    参数：
        session_id: 会话ID
        state_req: 状态请求，包含要导入的状态数据

    返回：
        导入结果
    """
    try:
        runtime = manager.get_session(session_id)
        success = runtime.import_state(state_req.state)
        if success:
            return {"success": True, "session_id": session_id}
        else:
            raise HTTPException(status_code=400, detail="状态导入失败")
    except KeyError:
        raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sessions/{session_id}/state/")
async def get_status(session_id: str, manager: SessionManager = Depends(get_session_manager)):
    """
    获取系统状态接口 - 会话级别

    参数：
        session_id: 会话ID

    返回：
        系统状态
    """
    try:
        runtime = manager.get_session(session_id)
        return {
            "success": True,
            "session_id": session_id,
            "state": {
                "step_count": runtime._runtime.step_count,
                "state": str(runtime._runtime.state)
            }
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"会话 {session_id} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    print("🚀 启动 PyClaw USB API 服务（多会话版本）")

    # 配置服务器参数
    server_host = "0.0.0.0"
    server_port = 8000

    print(f"📡 服务器地址: http://{server_host}:{server_port}")
    print(f"📚 API 文档: http://{server_host}:{server_port}/docs")
    print(f"📖 接口文档: http://{server_host}:{server_port}/redoc")
    print()
    print("🎯 可用接口:")
    print("  POST /sessions - 创建新会话")
    print("  GET /sessions - 列出所有会话")
    print("  GET /sessions/{id}/health - 检查会话健康状态")
    print("  DELETE /sessions/{id} - 删除会话")
    print("  POST /sessions/{id}/run - 执行任务")
    print("  GET /sessions/{id}/state/export - 导出状态")
    print("  POST /sessions/{id}/state/import - 导入状态")
    print("  GET /sessions/{id}/state/ - 获取系统状态")
    print("  GET /health - 健康检查")
    print("  GET /version - 获取版本信息")
    print()

    # 启动服务器
    uvicorn.run(
        app="server_multisession:app",
        host=server_host,
        port=server_port,
        reload=True
    )

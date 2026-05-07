#!/usr/bin/env python3
"""
PyClaw USB 后端 API 服务

提供远程访问 PyClaw 的 HTTP 接口，支持任务执行、状态导出和导入。
"""
import sys
import os
sys.path.insert(0, '/home/claw/.openclaw/workspace')

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any

# 导入 PyClaw API
from pyclaw import create_runtime


class TaskRequest(BaseModel):
    """任务请求模型"""
    task: str
    state: Dict[str, Any] = None


class StateRequest(BaseModel):
    """状态请求模型"""
    state: Dict[str, Any]


# 创建应用
app = FastAPI(title="PyClaw USB API", version="1.1")

# 配置 CORS 中间件（允许所有来源，生产环境应限制）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 PyClaw Runtime（服务器启动时创建）
runtime = create_runtime()


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "timestamp": "2026-05-03"}


@app.post("/run")
async def run_task(task_req: TaskRequest):
    """执行任务接口"""
    try:
        # 如果提供了状态，先导入
        if task_req.state:
            runtime.import_state(task_req.state)
        
        # 执行任务
        result = runtime.run(task_req.task)
        
        return {
            "success": True,
            "task": task_req.task,
            "result": str(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state/export")
async def export_state():
    """导出状态接口"""
    try:
        state = runtime.export_state()
        return {"success": True, "state": state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/state/import")
async def import_state(state_req: StateRequest):
    """导入状态接口"""
    try:
        success = runtime.import_state(state_req.state)
        if success:
            return {"success": True}
        else:
            raise HTTPException(status_code=400, detail="状态导入失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/")
async def get_memory():
    """获取记忆接口"""
    try:
        # 获取所有记忆内容
        # 注意：这里我们需要根据实际的 Runtime 接口调整
        return {"success": True, "memory": "memory not implemented"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/memory/")
async def clear_memory():
    """清除记忆接口"""
    try:
        # 清除记忆内容
        # 注意：这里我们需要根据实际的 Runtime 接口调整
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state/")
async def get_status():
    """获取系统状态接口"""
    try:
        return {
            "success": True,
            "state": {
                "step_count": runtime._runtime.step_count,
                "state": str(runtime._runtime.state)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/version")
async def get_version():
    """获取版本信息接口"""
    return {
        "success": True,
        "version": "1.1",
        "architecture": "PyClaw USB API Freeze Layer"
    }


if __name__ == "__main__":
    import uvicorn
    
    print("🚀 启动 PyClaw USB API 服务")
    
    # 配置服务器参数
    server_host = "0.0.0.0"
    server_port = 8000
    
    print(f"📡 服务器地址: http://{server_host}:{server_port}")
    print(f"📚 API 文档: http://{server_host}:{server_port}/docs")
    print(f"📖 接口文档: http://{server_host}:{server_port}/redoc")
    print()
    print("🎯 可用接口:")
    print("  POST /run - 执行任务")
    print("  GET /state/export - 导出状态")
    print("  POST /state/import - 导入状态")
    print("  GET /health - 健康检查")
    print("  GET /version - 获取版本信息")
    print("  GET /state/ - 获取系统状态")
    print()
    
    # 启动服务器
    uvicorn.run(
        app="server:app",
        host=server_host,
        port=server_port,
        reload=True
    )

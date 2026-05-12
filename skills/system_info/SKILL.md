---
name: system_info
description: 系统信息技能 - 查看系统信息、CPU/内存/磁盘使用、进程等
---

# 🖥️ 系统信息技能

PyClaw系统信息技能提供全面的系统监控和管理功能，帮助您快速了解系统资源使用情况。

## 🎯 核心功能

### 系统资源监控
- **CPU监控**：查看CPU使用情况、核心数、频率
- **内存监控**：查看内存使用情况、可用内存、缓存
- **磁盘监控**：查看磁盘空间使用情况、磁盘IO
- **网络监控**：查看网络连接、带宽使用情况

### 进程管理
- **进程列表**：查看正在运行的进程
- **进程搜索**：按名称或PID搜索进程
- **进程结束**：安全地结束指定进程

### 系统信息查看
- **操作系统信息**：查看操作系统版本、架构、内核信息
- **Python信息**：查看Python版本、路径信息
- **硬件信息**：查看CPU、内存、磁盘等硬件配置

## 🛠️ 工具列表

### 系统信息工具
```json
{
  "name": "system_info",
  "description": "获取系统基本信息，包括操作系统、Python版本、CPU、内存、磁盘等",
  "parameters": {}
}
```

### 进程列表工具
```json
{
  "name": "list_processes",
  "description": "列出当前运行的进程，支持按名称搜索和数量限制",
  "parameters": {
    "name": "进程名称（可选，支持部分匹配）",
    "limit": "显示数量限制（默认20）"
  }
}
```

### 进程结束工具
```json
{
  "name": "kill_process",
  "description": "结束指定PID的进程，支持强制结束",
  "parameters": {
    "pid": "要结束的进程PID",
    "force": "是否强制结束（默认false）"
  }
}
```

## 📝 使用示例

### 获取系统信息
```python
from pyclaw import Gateway

gateway = Gateway("api_key")

result = await gateway.call_tool("system_info", {})
print(result)
```

### 列出进程
```python
# 列出所有进程（默认显示20个）
result = await gateway.call_tool("list_processes", {})

# 按名称搜索进程
result = await gateway.call_tool("list_processes", {"name": "python"})

# 限制显示数量
result = await gateway.call_tool("list_processes", {"limit": 10})
```

### 结束进程
```python
# 正常结束进程
result = await gateway.call_tool("kill_process", {"pid": 12345})

# 强制结束进程（相当于kill -9）
result = await gateway.call_tool("kill_process", {"pid": 12345, "force": true})
```

## 📊 数据展示格式

### 系统信息输出
```markdown
🖥️ 系统信息

📦 系统信息
操作系统: Windows 10 Pro
版本: 10.0.19045
架构: AMD64
用户: JohnDoe

🐍 Python信息
版本: 3.12.3
路径: C:\\Python312\\python.exe

💻 硬件信息
CPU: Intel(R) Core(TM) i7-10700K CPU @ 3.80GHz
核心数: 8
线程数: 16
内存总量: 16.0 GB
可用内存: 10.5 GB
磁盘总容量: 512.0 GB
磁盘可用: 256.0 GB
```

### 进程列表输出
```markdown
📊 进程列表（显示前20个）

PID    CPU%  MEM%  名称
--------------------------
12345  0.1   2.5   python.exe
12346  0.5   1.2   chrome.exe
...
```

## 🐛 故障排除

### 常见问题及解决方案

#### 权限不足
```
错误: 无法访问系统信息（权限不足）
解决方案: 在Windows上以管理员身份运行，在Linux/macOS上使用sudo
```

#### 依赖库缺失
```
错误: 缺少psutil模块
解决方案: 安装psutil库: pip install psutil
```

#### 进程未找到
```
错误: 进程PID 12345不存在
解决方案: 确认PID是否正确，使用list_processes工具检查
```

#### 网络不可用
```
错误: 网络信息获取失败
解决方案: 检查网络连接，或重启网络服务
```

## 🔧 依赖要求

### 系统依赖
- **psutil**：进程和资源监控（需要安装）
- **platform**：操作系统信息（Python标准库）
- **sys**：系统信息（Python标准库）

### 安装依赖
```bash
pip install psutil
```

## 📚 技术细节

### 系统信息来源
- **Windows**：使用WMI、Windows API
- **Linux**：使用proc文件系统、sysfs、标准命令
- **macOS**：使用sysctl、mach APIs

### 性能优化
- 所有操作都是异步的，不会阻塞主线程
- 定期缓存系统信息，避免频繁查询
- 内存使用优化，只在需要时加载数据

## 🔄 版本更新

### v1.0.0（2024-05-12）
- 首次发布
- 支持系统信息查询
- 支持进程管理功能
- 支持Windows、Linux、macOS操作系统
- 优化了错误处理和用户反馈

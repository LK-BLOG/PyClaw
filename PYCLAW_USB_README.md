# PyClaw USB v1.0 - Portable AI Runtime

## 🚀 项目概述

PyClaw USB是一个**完全可移植的AI运行系统**，设计用于在任何计算机上运行而不需要安装依赖。它提供了一个安全的沙箱环境，确保AI操作不会对宿主系统造成影响，并支持任务状态的保存和恢复。

## 🎯 核心特性

### 1. 完全可移植性
- **零安装运行**：直接运行，无需pip或系统依赖
- **可迁移状态**：任务状态保存在`snapshot.json`中，复制到新系统可继续执行
- **无路径依赖**：所有操作均相对于沙箱目录

### 2. 安全沙箱环境
- **严格的文件访问控制**：所有操作限制在`sandbox/workspace/`目录内
- **禁止系统访问**：阻止对系统目录（如/etc, /sys, C:/Windows）的访问
- **相对路径默认处理**：无前缀路径默认到workspace目录

### 3. 状态管理
- **状态保存**：每步执行后自动保存到`snapshot.json`
- **状态恢复**：启动时可选择恢复之前的任务
- **任务ID跟踪**：唯一标识符确保任务一致性

### 4. 执行追踪
- **详细的执行链记录**：保存到`state/trace.json`
- **实时状态显示**：显示当前执行步骤和结果
- **安全策略拦截**：显示被阻止的操作及原因

### 5. 分层架构
- **Planner**：任务拆解和规划
- **Executor**：工具执行
- **Evaluator**：执行结果判断
- **Replan**：失败重规划
- **Memory**：状态管理和记录

## 🏗️ 文件结构

```
PyClaw_USB/
├── pyclaw/
│   ├── run.py                  # 主运行入口
│   ├── bootstrap.py            # 系统初始化
│   ├── core/
│   │   ├── runtime.py          # 执行引擎
│   │   ├── planner.py          # 任务规划
│   │   ├── evaluator.py        # 结果评估
│   │   └── trace.py            # 执行追踪
│   ├── llm/
│   │   ├── client.py           # LLM接口
│   │   └── prompt_builder.py   # 提示生成
│   ├── policy/
│   │   └── execution_policy.py # 安全策略
│   ├── tools/
│   │   ├── file_tool.py        # 沙箱化文件操作
│   │   ├── bash_tool.py        # bash执行
│   │   └── python_tool.py      # Python执行
│   ├── memory/
│   │   ├── short_term.py       # 短期记忆
│   │   └── state_store.py      # 状态存储
│   ├── sandbox/
│   │   ├── fs_guard.py         # 文件访问限制
│   │   └── workspace/          # 唯一可写目录
│   ├── state/                  # 状态存储目录
│   └── logs/                   # 日志目录
└── test_*.py                  # 测试脚本
```

## 🚀 快速开始

### 1. 启动PyClaw
```bash
cd /path/to/PyClaw_USB
python3 pyclaw/run.py
```

### 2. 使用流程
1. 启动后会检查是否有之前的任务状态
2. 输入任务内容（如"创建一个简单的Python脚本"）
3. PyClaw会自动规划并执行任务
4. 每步执行后会保存状态到`pyclaw/state/snapshot.json`

### 3. 恢复执行
如果PyClaw检测到之前的状态，会询问是否要恢复执行：
```
🔄 检测到之前的状态，任务ID: 20260503-080700
📋 当前步骤: 2
是否要恢复执行? (y/n, 默认n): y
```

### 4. 暂停执行
在任何时刻按`p`键或`q`键暂停执行，状态会自动保存。

## 🧪 测试系统

### 运行完整功能测试
```bash
python3 -c '
import sys
sys.path.insert(0, "/home/claw/.openclaw/workspace")
from test_usb_architecture import main
main()
'
```

### 预期输出
```
🎯 USB架构功能测试
==================================================

🧪 测试沙箱化功能
--------------------------------------------------
✅ 工作区目录已创建
✅ 允许访问: ./pyclaw/sandbox/workspace/test.txt
✅ 相对路径访问: test.txt
✅ 禁止访问系统目录: /etc/passwd
✅ 禁止访问上级目录: ../../../../../etc/passwd
✅ 禁止访问Windows系统目录: C:/Windows/System32


🧪 测试状态存储和加载
--------------------------------------------------
✅ 状态已保存到: state/snapshot.json
✅ 状态保存成功
✅ 状态已加载: state/snapshot.json
✅ 状态加载成功
✅ 状态内容验证通过
✅ 状态已清除
✅ 状态清除成功


🧪 测试启动过程
--------------------------------------------------
🚀 正在启动PyClaw USB Runtime...
✅ 安全策略层初始化完成
✅ 运行时引擎初始化完成
✅ 沙箱化工具链注册完成
🎉 PyClaw USB Runtime启动成功
✅ Runtime初始化成功
✅ 工具链已注册 (4个工具)

🧪 测试基本功能
--------------------------------------------------
✅ 任务规划成功 (共 3 步)
✅ 单步执行成功

==================================================
📊 测试结果: 4/4 通过
🎉 所有测试通过！USB架构功能正常
```

## 🔒 安全保障

### 禁止操作
- 访问系统目录（如/etc/passwd, C:/Windows/System32）
- 执行系统命令（如rm -rf /, format C:）
- 网络访问（默认禁止，可配置）
- 文件操作到允许目录之外

### 限制机制
- 文件系统访问限制器（FileGuard）
- 执行策略（ExecutionPolicy）
- 沙箱化工具执行
- 任务状态验证

## 📈 性能优化

### 执行策略
- 内存限制（2GB）
- 执行时间限制（10分钟/任务）
- 文件大小限制（100MB/文件）
- 输出限制（1000行/命令）

## 🚀 未来版本

### v1.1 计划
- 插件系统支持
- GUI界面
- 任务队列管理
- 加密状态存储
- 离线LLM支持

### v1.2 计划
- 多任务并行执行
- 可视化执行流程
- 策略配置文件
- 性能监控

## 📚 开发说明

### 架构原则
1. **严格分层**：Planner、Executor、Evaluator、Memory完全分离
2. **状态驱动**：所有执行状态化，可序列化
3. **安全优先**：默认拒绝，白名单允许
4. **可移植性**：不依赖系统特定功能

### 工具开发规范
```python
from pyclaw.sandbox.fs_guard import FileGuard

def my_safe_function(param):
    safe_path = FileGuard.safe_path(param)
    # 只在safe_path内进行操作
```

## 🐛 调试和故障排除

### 常见问题

#### 1. 状态加载失败
```
❌ 加载状态失败: JSONDecodeError
```
解决：删除`state/snapshot.json`重新开始。

#### 2. 权限拒绝
```
❌ ACCESS DENIED: Path '/etc/passwd' not in allowed directories
```
解决：确保操作路径在workspace目录内。

#### 3. 执行超时
```
❌ 命令执行超时（30秒）
```
解决：检查任务复杂度，或增加超时限制。

## 📄 许可证

PyClaw USB版采用MIT许可证，可自由使用和修改。

---

## 🌟 总结

PyClaw USB v1.0实现了**完全可移植的AI运行系统**，具备：

✅ 沙箱化安全执行
✅ 任务状态管理
✅ 状态保存和恢复
✅ 完整的执行追踪
✅ 严格的安全策略

这是一个非常接近产品级的AI运行单元，提供了良好的开发体验和安全保障。

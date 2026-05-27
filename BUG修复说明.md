# 🐛 PyClaw Bug 修复总结

## 修复日期
2026-04-27

---

## 问题 1：`ToolCall has no attribute 'parameters'`
**状态：✅ 已修复**

### 现象
```
AttributeError: 'ToolCall' object has no attribute 'parameters'
```

### 原因
- `ToolCall` 类定义的字段是 `arguments`
- 但旧代码里写成了 `tc.parameters`

### 修复位置
`webapp.py` 第 646 行：
```python
# 修复前
"arguments": json.dumps(tc.parameters, ensure_ascii=False)

# 修复后  
"arguments": json.dumps(tc.arguments, ensure_ascii=False)
```

---

## 问题 2：BAT 脚本中文乱码，无法启动
**状态：✅ 已修复**

### 现象
```
'帴璁块棶锛?set' 不是内部或外部命令
'py' 不是内部或外部命令
```

### 原因
- BAT 文件保存为 UTF-8 编码
- Windows CMD 默认用 GBK 编码打开，导致中文乱码
- 乱码导致命令解析失败

### 修复方案
创建了 GBK 编码的修复版脚本：
- `启动_修复版.bat` - 用英文提示，避免编码问题
- `清理_修复版.bat` - 用英文提示，避免编码问题

### 临时解决方案
**不要双击 BAT 文件！** 直接在 CMD 里运行：
```cmd
cd F:\pyclaw
python3 run.py
```

---

## 问题 3：DeepSeek 把思考过程当成回答
**状态：✅ 已优化**

### 现象
- 模型输出类似「让我思考一下...」「我需要调用工具...」
- 把内部推理过程直接展示给用户

### 修复方案
在 `agent.py` 的 system prompt 里添加了强制约束：
```
⚠️ 输出格式强制要求：
1. **直接给出最终答案**，不要输出任何思考过程、推理步骤或内部独白
2. 不要用「我需要思考一下」「让我分析」这类过渡语
3. 不要重复用户的问题
4. 工具调用会在后台自动处理，不要向用户解释你要调用什么工具
```

---

## 问题 4：DeepSeek API 连接中断
**状态：⚠️ 网络问题**

### 现象
```
httpx.RemoteProtocolError: Server disconnected without sending a response.
```

### 原因
- DeepSeek API 服务器不稳定
- 或网络连接超时

### 建议
1. 检查网络连接
2. 更换为其他模型 API（豆包、Qwen 等）
3. 增加超时时间

---

## 使用说明

### 推荐启动方式
```cmd
# 进入 pyclaw 目录后直接运行
python3 run.py
```

### 文件说明（已统一）
| 文件 | 平台 | 说明 |
|------|------|------|
| `启动.sh` | 🐧 Linux | ✅ 保留原有，Linux 原生 |
| `启动.bat` | 🪟 Windows + 🍷 Wine | 统一版，同时兼容 Windows CMD 和 Wine |
| `清理.sh` | 🐧 Linux | ✅ 保留原有，Linux 原生 |
| `清理.bat` | 🪟 Windows + 🍷 Wine | 统一版，同时兼容 Windows CMD 和 Wine |

### 启动方式

**Linux 用户（推荐）**：
```bash
./启动.sh
# 或者直接
python3 run.py
```

**Windows 用户**：
```cmd
双击 启动.bat
# 或者 CMD 中运行
启动.bat
```

**Wine 测试（Linux 下模拟 Windows）**：
```bash
wine cmd /c 启动.bat
```

# 📺 Bilibili Skill - PyClaw 完整版

## ✨ 功能特性

- ✅ **发布纯文字动态** - 支持自定义内容、话题标签
- ✅ **发布隧道更新动态** - 自动读取 Cloudflare Tunnel 链接，多种风格可选
- ✅ **扫码登录** - 生成二维码，手机扫码即可登录
- ✅ **登录状态检查** - 验证 Cookie 是否有效
- ✅ **日常风格模板** - 内置口语化的动态内容模板

## 🔧 工具列表

### 1. `bilibili_publish_dynamic` - 发布自定义动态
**参数:**
- `content` - 动态内容（必填）
- `cookie_file` - Cookie 文件路径（可选）

### 2. `bilibili_publish_tunnel_dynamic` - 发布隧道更新动态
**参数:**
- `tunnel_url` - 隧道链接（可选，自动读取）
- `style` - 风格：`casual`（日常）| `formal`（正式）| `simple`（简洁）

### 3. `bilibili_qr_login` - 扫码登录
**参数:**
- `save_path` - Cookie 保存路径（可选）
- `timeout` - 超时时间（秒，可选）

### 4. `bilibili_check_login` - 检查登录状态
**参数:**
- `cookie_file` - Cookie 文件路径（可选）

## 📝 使用方法

### 第一步：扫码登录
```python
# 在 PyClaw 中调用
bilibili_qr_login()
```

然后用 B站 App 扫描生成的二维码即可登录。

### 第二步：发布动态
```python
# 发布自定义动态
bilibili_publish_dynamic(content="Hello, PyClaw! #PyClaw #AI")

# 发布隧道更新动态（日常风格）
bilibili_publish_tunnel_dynamic(style="casual")
```

## 📁 文件结构

```
skills/bilibili/
├── __init__.py      # 主 Skill 文件（所有功能）
├── Cookie.txt       # 登录凭证（扫码后自动生成）
└── README.md        # 本说明文档
```

## ⚠️ 注意事项

1. **Cookie 安全**：Cookie.txt 包含登录凭证，不要分享给他人
2. **有效期**：B站 Cookie 通常有效期约 1 个月，过期后重新扫码即可
3. **依赖安装**：需要 `bilibili-api-python` 包
   ```bash
   pip install bilibili-api-python
   ```

## 🔄 版本历史

- **v2.0.0** - 完整版：集成扫码登录、隧道动态发布、状态检查等所有功能
- **v1.0.0** - 基础版：仅支持发布纯文字动态

---

*由 PyClaw Team 维护 🦞*

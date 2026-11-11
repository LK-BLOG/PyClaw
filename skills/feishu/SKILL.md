---
name: feishu
version: 1.0.0
description: "飞书即时通讯：通过 exec + httpx 发送消息、管理机器人。当用户需要发送飞书消息时使用此技能。"
metadata:
  requires:
    bins: ["python3"]
  configKeys:
    - FEISHU_APP_ID
    - FEISHU_APP_SECRET
---

# feishu (v1)

## 前置条件

在 `pyclaw.json` 中配置飞书应用凭证：

```json
{
  "FEISHU_APP_ID": "cli_xxxxxxxxxxxxxx",
  "FEISHU_APP_SECRET": "xxxxxxxxxxxxxxxxxxxxxxxx"
}
```

飞书开放平台 → 创建企业自建应用/智能体 → 拿到 APP_ID 和 APP_SECRET。

## 认证

所有 API 调用前需要先获取 `tenant_access_token`（机器人身份），通过 **exec** + `httpx`：

```python
# 获取 tenant_access_token
import httpx, json
r = httpx.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": "APP_ID", "app_secret": "APP_SECRET"}, timeout=10)
print(json.dumps(r.json(), ensure_ascii=False))
```

成功返回：
```json
{"code": 0, "tenant_access_token": "t-xxxxxxxxxxxxx", "expire": 7200}
```

> token 有效期 2 小时，建议每次发消息前重新获取。

## 发送文本消息

```python
import httpx, json

APP_ID = "cli_xxx"    # 从 pyclaw.json 读取
APP_SECRET = "xxx"    # 从 pyclaw.json 读取
receive_id_type = "open_id"   # 或 chat_id / user_id
receive_id = "oc_xxxxx"

# 1. 获取 token
r = httpx.post("https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    json={"app_id": APP_ID, "app_secret": APP_SECRET}, timeout=10)
token = r.json()["tenant_access_token"]

# 2. 发消息
r = httpx.post(
    f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={receive_id_type}",
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    json={"receive_id": receive_id, "msg_type": "text",
          "content": json.dumps({"text": "你好"}, ensure_ascii=False)},
    timeout=10)
print(json.dumps(r.json(), ensure_ascii=False, indent=2))
```

## 发送富文本消息

```python
content = json.dumps({
    "zh_cn": {
        "title": "标题",
        "content": [
            [{"tag": "text", "text": "第一行 "},
             {"tag": "a", "text": "链接", "href": "https://example.com"}],
            [{"tag": "text", "text": "第二行"}]
        ]
    }
}, ensure_ascii=False)
# msg_type 改为 "post"
r = httpx.post(..., json={"receive_id": id, "msg_type": "post", "content": content})
```

## 发送卡片消息

构建卡片 JSON（参照飞书开放平台卡片模板），`msg_type` 设为 `"interactive"`。

## 错误处理

| code | 含义 | 处理方式 |
|------|------|----------|
| 0 | 成功 | - |
| 99991663 | token 过期 | 重新获取 token 再试 |
| 10003 | 缺少权限 | 检查应用权限配置 |
| 230001 | 内容格式错误 | 检查 JSON 格式 |
| 99991668 | 频率限制 | 等待后重试 |

## 一行搞定（示例）

```powershell
python -c "import httpx, json; r=httpx.post('https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal', json={'app_id':'cli_xxx','app_secret':'xxx'}, timeout=10); t=r.json()['tenant_access_token']; r=httpx.post('https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id', headers={'Authorization':f'Bearer {t}'}, json={'receive_id':'oc_xxx','msg_type':'text','content':json.dumps({'text':'你好'})}, timeout=10); print(r.json())"
```

> 实际使用时代入 `pyclaw.json` 中的凭证和目标 ID。

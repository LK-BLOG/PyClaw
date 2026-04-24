# 📂 Workspace Skill - PyClaw 工作空间管理

## ✨ 功能特性

- ✅ **添加工作空间** - 给常用目录起个名字，方便快速访问
- ✅ **列出工作空间** - 查看所有已添加的工作空间
- ✅ **移除工作空间** - 从列表中移除（不会删除实际文件）
- ✅ **浏览目录** - 查看工作空间内的文件和目录结构
- ✅ **读取文件** - 读取文本文件内容，支持行数限制
- ✅ **搜索文件** - 按文件名搜索（支持通配符）
- ✅ **Git 状态** - 查看 Git 仓库状态、修改的文件、当前分支

## 🔧 工具列表

### 1. `workspace_add` - 添加工作空间
**参数:**
- `name` - 工作空间名称（简短好记）
- `path` - 目录路径（绝对路径或相对路径）

**示例:**
```python
workspace_add(name="我的项目", path="/Users/xxx/Projects/my-project")
```

### 2. `workspace_list` - 列出所有工作空间
**参数:** 无

**示例:**
```python
workspace_list()
```

### 3. `workspace_remove` - 移除工作空间
**参数:**
- `name` - 要移除的工作空间名称

**示例:**
```python
workspace_remove(name="旧项目")
```

### 4. `workspace_files` - 浏览目录内容
**参数:**
- `workspace` - 工作空间名称
- `subdir` - （可选）子目录路径
- `show_hidden` - （可选）是否显示隐藏文件，默认 false

**示例:**
```python
# 浏览工作空间根目录
workspace_files(workspace="我的项目")

# 浏览子目录
workspace_files(workspace="我的项目", subdir="src")
```

### 5. `workspace_read_file` - 读取文件内容
**参数:**
- `workspace` - 工作空间名称
- `file_path` - 文件路径（相对于工作空间）
- `limit` - （可选）最大读取行数，默认 100 行

**示例:**
```python
workspace_read_file(workspace="我的项目", file_path="README.md", limit=50)
```

### 6. `workspace_search` - 搜索文件
**参数:**
- `workspace` - 工作空间名称
- `pattern` - 搜索关键词（支持通配符，如 `*.py`）

**示例:**
```python
# 搜索所有 Python 文件
workspace_search(workspace="我的项目", pattern="*.py")

# 搜索包含 "test" 的文件
workspace_search(workspace="我的项目", pattern="*test*")
```

### 7. `workspace_git_status` - 查看 Git 状态
**参数:**
- `workspace` - 工作空间名称

**示例:**
```python
workspace_git_status(workspace="我的项目")
```

## 📁 文件结构

```
skills/workspace/
├── __init__.py      # 主 Skill 文件
└── README.md        # 本说明文档
```

## 💡 使用技巧

1. **添加常用目录** - 把经常访问的项目目录添加为工作空间
2. **使用描述性名称** - 比如"博客源码"、"Python 练习"、"毕业设计"
3. **先浏览再读取** - 先用 `workspace_files` 浏览目录，再读取具体文件
4. **搜索快速定位** - 不确定文件位置时用 `workspace_search` 搜索

## 🔒 安全限制

- 不能访问工作空间以外的目录（防止跳出工作空间）
- 读取文件大小限制为 1MB（保护大文件）
- 文件名搜索最多显示 50 个结果
- 隐藏文件默认不显示（可手动开启）

## 📊 配置文件

工作空间列表保存在：
```
~/.pyclaw/workspaces.json
```

格式为 JSON，名称到路径的映射。

---

*由 PyClaw Team 维护 🦞*

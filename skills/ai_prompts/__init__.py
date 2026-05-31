"""
AI Prompts Skill — 品牌 AI 提示词合集

提供 33 个品牌的 108 个系统提示词检索与搜索功能。
数据来源：System Prompts and Models of AI Tools
"""
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Any


# ── 模块级常量 ────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")
SKILL_NAME = "ai_prompts"
SKILL_VERSION = "1.0.0"
SKILL_AUTHOR = "PyClaw"
SKILL_DESCRIPTION = "33 个品牌的 108 个 AI 系统提示词合集，支持全文搜索与分类浏览"


# ── 元数据 ────────────────────────────────────────
class SkillMetadata:
    """Skill 元数据（与 pyclaw.skill.SkillMetadata 兼容）"""
    def __init__(self):
        self.name = "AI Prompts"
        self.description = SKILL_DESCRIPTION
        self.author = SKILL_AUTHOR
        self.version = SKILL_VERSION
        self.tags = ["ai", "prompts", "system-prompts", "brands", "search"]
        self.website = None


# ── 索引结构 ──────────────────────────────────────
# {
#   "brands": [
#     {
#       "name": "BrandName",
#       "files": [
#         {"name": "file.md", "path": "/abs/path/file.md", "preview": "first 200 chars"}
#       ]
#     }
#   ],
#   "full_text": {
#     "BrandName/file.md": "full content"
#   }
# }


# ── 内部工具函数 ─────────────────────────────────
def _scan_prompts() -> Dict[str, Any]:
    """扫描 prompts/ 目录，构建品牌-文件索引"""
    brands = []
    full_text = {}

    if not os.path.isdir(DATA_DIR):
        return {"brands": brands, "full_text": full_text}

    for entry in sorted(os.listdir(DATA_DIR)):
        brand_dir = os.path.join(DATA_DIR, entry)
        if not os.path.isdir(brand_dir) or entry.startswith("."):
            continue

        files = []
        for fname in sorted(os.listdir(brand_dir)):
            if not (fname.endswith(".md") or fname.endswith(".txt")):
                continue
            fpath = os.path.join(brand_dir, fname)
            key = f"{entry}/{fname}"

            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                    content = fh.read()
            except Exception:
                content = ""

            preview = content[:200].strip()
            if not preview:
                preview = "(empty file)"

            files.append({
                "name": fname,
                "path": fpath,
                "preview": preview,
            })
            full_text[key] = content

        if files:
            brands.append({"name": entry, "files": files})

    return {"brands": brands, "full_text": full_text}


# ── 工具定义 ──────────────────────────────────────
class ListAITools:
    """list_ai_tools — 列出所有品牌的提示词"""

    @property
    def definition(self) -> Any:
        from pyclaw.pyclaw_types import ToolDefinition
        return ToolDefinition(
            name="list_ai_tools",
            description="列出所有品牌的 AI 提示词，可选按关键词筛选品牌",
            parameters={
                "type": "object",
                "properties": {
                    "filter": {
                        "type": "string",
                        "description": "可选，按品牌名或文件名关键词筛选",
                    }
                },
                "required": [],
            },
        )

    async def execute(self, params: Dict[str, Any]) -> Any:
        from pyclaw.pyclaw_types import ToolResult

        keyword = (params.get("filter") or "").strip().lower()
        index = _scan_prompts()
        brands = index["brands"]

        if keyword:
            filtered = []
            for brand in brands:
                bn_lower = brand["name"].lower()
                if keyword in bn_lower:
                    filtered.append(brand)
                    continue
                # check file names
                matched_files = [
                    f for f in brand["files"]
                    if keyword in f["name"].lower()
                ]
                if matched_files:
                    filtered.append({"name": brand["name"], "files": matched_files})
            brands = filtered

        if not brands:
            return ToolResult(
                success=True,
                content="未找到匹配的 AI 提示词品牌。" if not keyword else f"未找到包含「{keyword}」的品牌或文件。",
            )

        lines = [f"📚 AI 提示词品牌列表（共 {len(brands)} 个）"]
        lines.append("=" * 60)
        for brand in brands:
            lines.append(f"\n🏷️  {brand['name']} ({len(brand['files'])} 个文件)")
            lines.append("-" * 40)
            for f in brand["files"]:
                preview_short = f["preview"].replace("\n", " ")[:80]
                lines.append(f"  📄 {f['name']}")
                lines.append(f"     ▸ {preview_short}...")

        return ToolResult(success=True, content="\n".join(lines))


class GetAIPrompt:
    """get_ai_prompt — 获取指定品牌的提示词"""

    @property
    def definition(self) -> Any:
        from pyclaw.pyclaw_types import ToolDefinition
        return ToolDefinition(
            name="get_ai_prompt",
            description="获取指定品牌的 AI 提示词内容。不指定 file 参数则列出该品牌的所有文件；指定 file 则返回该文件全文。",
            parameters={
                "type": "object",
                "properties": {
                    "brand": {
                        "type": "string",
                        "description": "品牌名称（不区分大小写），例如 openai, claude, deepseek",
                    },
                    "file": {
                        "type": "string",
                        "description": "可选，文件名（不区分大小写），例如 cursor.txt 或 system-prompt.md",
                    },
                },
                "required": ["brand"],
            },
        )

    async def execute(self, params: Dict[str, Any]) -> Any:
        from pyclaw.pyclaw_types import ToolResult

        brand_query = (params.get("brand") or "").strip().lower()
        file_query = (params.get("file") or "").strip().lower()

        if not brand_query:
            return ToolResult(success=False, content="", error="请提供品牌名称。")

        index = _scan_prompts()
        # 不区分大小写匹配品牌
        matched_brand = None
        for brand in index["brands"]:
            if brand["name"].lower() == brand_query:
                matched_brand = brand
                break

        # 品牌名模糊匹配（部分匹配）
        if not matched_brand:
            candidates = [
                b for b in index["brands"]
                if brand_query in b["name"].lower()
            ]
            if len(candidates) == 1:
                matched_brand = candidates[0]
            elif len(candidates) > 1:
                names = "\n".join(f"  - {b['name']}" for b in candidates)
                return ToolResult(
                    success=True,
                    content=f"找到多个匹配「{params['brand']}」的品牌：\n{names}\n\n请使用完整品牌名称。",
                )

        if not matched_brand:
            all_names = "\n".join(f"  - {b['name']}" for b in index["brands"])
            return ToolResult(
                success=True,
                content=f"未找到品牌「{params['brand']}」。\n可用的品牌：\n{all_names}" if all_names else "暂无可用品牌数据，请确认 prompts/ 目录已正确安装。",
            )

        # 不指定 file → 列出该品牌所有文件
        if not file_query:
            lines = [f"🏷️  {matched_brand['name']}（{len(matched_brand['files'])} 个文件）"]
            lines.append("=" * 60)
            for f in matched_brand["files"]:
                preview_short = f["preview"].replace("\n", " ")[:120]
                lines.append(f"\n📄 {f['name']}")
                lines.append(f"   {preview_short}...")
            return ToolResult(success=True, content="\n".join(lines))

        # 指定 file → 匹配文件
        matched_file = None
        for f in matched_brand["files"]:
            if f["name"].lower() == file_query:
                matched_file = f
                break
        if not matched_file:
            for f in matched_brand["files"]:
                if file_query in f["name"].lower():
                    matched_file = f
                    break

        if not matched_file:
            file_list = "\n".join(f"  - {f['name']}" for f in matched_brand["files"])
            return ToolResult(
                success=True,
                content=f"未找到文件「{params['file']}」。\n{matched_brand['name']} 下的文件：\n{file_list}",
            )

        # 读取完整内容
        try:
            with open(matched_file["path"], "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except Exception as e:
            return ToolResult(success=False, content="", error=f"读取文件失败：{e}")

        lines = [
            f"🏷️  {matched_brand['name']} / 📄 {matched_file['name']}",
            "=" * 60,
            "",
            content,
        ]
        return ToolResult(success=True, content="\n".join(lines))


class SearchAIPrompts:
    """search_ai_prompts — 在所有提示词内容中搜索关键词"""

    @property
    def definition(self) -> Any:
        from pyclaw.pyclaw_types import ToolDefinition
        return ToolDefinition(
            name="search_ai_prompts",
            description="在所有品牌的 AI 提示词内容中搜索关键词，返回匹配的品牌、文件名及片段",
            parameters={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "要搜索的关键词",
                    }
                },
                "required": ["keyword"],
            },
        )

    async def execute(self, params: Dict[str, Any]) -> Any:
        from pyclaw.pyclaw_types import ToolResult

        keyword = (params.get("keyword") or "").strip()
        if not keyword:
            return ToolResult(success=False, content="", error="请提供搜索关键词。")

        index = _scan_prompts()
        results = []

        for key, content in index["full_text"].items():
            if keyword.lower() in content.lower():
                brand_name, file_name = key.split("/", 1)
                # 提取匹配片段
                idx = content.lower().find(keyword.lower())
                start = max(0, idx - 80)
                end = min(len(content), idx + len(keyword) + 80)
                snippet = content[start:end]
                if start > 0:
                    snippet = "..." + snippet
                if end < len(content):
                    snippet = snippet + "..."

                results.append({
                    "brand": brand_name,
                    "file": file_name,
                    "snippet": snippet,
                })

        if not results:
            return ToolResult(
                success=True,
                content=f"在 {len(index['full_text'])} 个文件中未找到包含「{keyword}」的内容。",
            )

        lines = [f"🔍 搜索关键词「{keyword}」— 共 {len(results)} 条结果"]
        lines.append("=" * 60)
        for r in results:
            lines.append(f"\n🏷️  {r['brand']} / 📄 {r['file']}")
            lines.append(f"   {r['snippet']}")

        return ToolResult(success=True, content="\n".join(lines))


# ── 主 Skill 类 ──────────────────────────────────
SKILL_CLASS = "AIPromptsSkill"


class AIPromptsSkill:
    """AI 提示词合集 Skill"""

    def __init__(self):
        self._metadata = SkillMetadata()
        self._initialized = False
        self._brands: List[Dict] = []
        self._counts = {"brands": 0, "files": 0}

    @property
    def metadata(self) -> SkillMetadata:
        return self._metadata

    def get_tools(self) -> List[Any]:
        return [ListAITools(), GetAIPrompt(), SearchAIPrompts()]

    async def initialize(self) -> bool:
        """加载索引，扫描提示词目录"""
        if self._initialized:
            return True

        index = _scan_prompts()
        self._brands = index["brands"]
        self._counts["brands"] = len(self._brands)
        self._counts["files"] = sum(len(b["files"]) for b in self._brands)
        self._initialized = True

        print(f"[OK] AIPromptsSkill 初始化完成：{self._counts['brands']} 个品牌，{self._counts['files']} 个提示词文件")
        return True

    async def cleanup(self) -> None:
        """清理资源"""
        self._brands = []
        self._initialized = False
        self._counts = {"brands": 0, "files": 0}

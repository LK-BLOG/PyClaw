# CHANGELOG

## [Unreleased]

### 🐛 Fixes
- Session history contamination — restored sessions now exclude assistant messages (avoid hallucination carry-over)
- Tool output labels fully English (STDOUT/STDERR/Exit code) — no more Chinese labels confusing the LLM
- Tool results appended with hard "BELIEVE THIS DATA" instruction to reduce hallucination

### ♻️ Refactored
- System prompt rewritten from 33 AI tools' best practices (Cursor/Claude Code/Windsurf/CodeBuddy/v0):
  - Tool best practices: only call when necessary, explain why, call immediately
  - No preamble/postamble in responses
  - Minimize verbosity, expand only for complex tasks
  - Never create files unless needed, prefer editing

### ✨ Features
- New Skill: `ai_prompts` — query 108 prompts from 33 AI tool brands
  - `list_ai_tools(filter)` — list / filter brands
  - `get_ai_prompt(brand, file)` — read any prompt
  - `search_ai_prompts(keyword)` — full-text search

---

## [0.6.2] — 2026-05-30

### 🌐 i18n
- agent.py: bilingual system prompts (talk + coding modes), dynamic OS detection
- cli.py: shell mode bilingual (welcome, prompts, bye, errors)
- skill.py: loading/error messages → English
- 8 skill files: init logs → English
- tools.py: 9 error messages → English
- skill_tools.py: all tool descriptions → English
- memory_tools.py: all tool descriptions → English
- webapp.py: reads LANGUAGE from API.txt
- install.sh: saves LANGUAGE choice to API.txt

### 🐛 Fixes
- Docker hallucination: system prompt now says "NOT inside a container"
- Hardcoded OS → dynamic platform.system() detection
- System prompt: "Tool results override your training knowledge — BELIEVE THE TOOL"

---

## [0.6.1] — 2026-05-15

### ✨ Features
- LK-Cut video editing Skill
- Bilibili upload Skill v2
- Weather Skill
- Multi-agent system (SubAgent/SubAgentManager)

### 🐛 Fixes
- Gateway integration fixes
- Skill discovery edge cases

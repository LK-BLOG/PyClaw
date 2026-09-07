#!/usr/bin/env python3
"""
PyClaw NSIS 安装包构建器
========================
步骤:
  1. 把项目拷贝到 build\\staging（剔除 .git / 缓存 / 运行时数据）
  2. 调用 NSIS makensis 编译 installer.nsi
  3. 产出 PyClaw-for-Windows-Setup.exe

用法:
  python build_installer.py
可配置:
  --makensis   makensis.exe 完整路径（默认自动探测）
  --out        输出 exe 完整路径（默认项目根目录）
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGE = ROOT / "build" / "staging"
EXCLUDE_DIRS = {
    ".git", ".sessions", ".pytest_cache", "__pycache__", ".codex",
    ".pyclaw_webview", "pyclaw_data", "build", "dist", "venv",
    "python_portable", ".claude", "node_modules", "workspace",
    ".learnings", ".venv", "wiki", ".idea", ".vscode", "tests", "docs",
}
EXCLUDE_FILES = {
    ".pyc", ".pyo", ".log", ".db", ".sqlite", ".obj", ".tmp", ".wixobj",
    ".wixpdb", ".caf", ".pyd", ".zip", ".pptx", ".exe", ".pid",
}
# 敏感文件：无论如何不打包（含 API Key / 用户会话 / 记忆）
SENSITIVE = {
    "pyclaw.json", "pyclaw.local.json", "API.txt", "volc_api.txt",
    ".env", ".pyclaw.pid", ".pyclaw.pidlock", "pyclaw-issue-check.json",
    "pyclaw_memory.db", ".pyclaw_desktop.log",
}
# 已生成的安装/卸载产物，不要打进新包
FORCE_EXCLUDE = {
    "uninstall.exe", "PyClaw-for-Windows-Setup.exe", "PyClaw_for_Windows.exe",
    "PyClaw-for-Windows.exe", "PyClaw-for-Windows.zip", "PyClaw_Installer.zip",
    "PyClaw_Installer.exe", "installer.nsi", "build_installer.py",
}


def find_makensis():
    env = os.environ.get("NSIS_HOME")
    if env:
        p = Path(env) / "makensis.exe"
        if p.exists():
            return str(p)
    for cand in [
        r"D:\NSIS\makensis.exe",
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
        "makensis",
    ]:
        if cand == "makensis":
            import shutil as _sh
            if _sh.which(cand):
                return cand
        elif Path(cand).exists():
            return cand
    return None


def exclude(path: Path) -> bool:
    if path.name in FORCE_EXCLUDE or path.name in SENSITIVE:
        return True
    if path.suffix.lower() in EXCLUDE_FILES:
        return True
    if path.is_dir() and path.name in EXCLUDE_DIRS:
        return True
    return False


def stage():
    print(f"[1/3] 准备打包目录: {STAGE}")
    if STAGE.exists():
        shutil.rmtree(STAGE)
    STAGE.mkdir(parents=True, exist_ok=True)

    for item in ROOT.iterdir():
        if item in (Path(".git"), STAGE):
            continue
        if item.name.endswith(".egg-info"):
            continue
        if item.name in SENSITIVE:
            continue
        if item.name in EXCLUDE_DIRS or item.name in FORCE_EXCLUDE:
            continue
        if item.suffix.lower() in EXCLUDE_FILES:
            continue
        dest = STAGE / item.name
        if item.is_dir():
            shutil.copytree(
                item, dest,
                ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "*.log", "*.db", ".git",
                    ".pytest_cache", ".codex", ".sessions", "build",
                    "pyclaw.json", "pyclaw.local.json", "API.txt",
                    "volc_api.txt", ".env", "*.egg-info",
                ),
            )
        else:
            shutil.copy2(item, dest)
    print(f"  已拷贝 {sum(1 for _ in STAGE.rglob('*'))} 个文件")


def build(makensis: str):
    nsi = ROOT / "installer.nsi"
    out = ROOT / "PyClaw-for-Windows-Setup.exe"
    print(f"[2/3] 编译 NSI: {nsi}")
    cmd = [makensis, nsi.name]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print("[ERROR] makensis 编译失败:")
        print(r.stderr or r.stdout)
        return False
    if out.exists():
        print(f"[3/3] 生成: {out} ({out.stat().st_size // 1024} KB)")
        return True
    print("[ERROR] 未找到输出 exe")
    return False


def main():
    args = sys.argv[1:]
    makensis = None
    if "--makensis" in args:
        i = args.index("--makensis")
        makensis = args[i + 1]
    if not makensis:
        makensis = find_makensis()
    if not makensis:
        print("[ERROR] 未找到 makensis.exe，请安装 NSIS 或用 --makensis 指定路径")
        sys.exit(1)
    print(f"使用 makensis: {makensis}")
    stage()
    ok = build(makensis)
    # 清理 staging（保留 exe）
    build_dir = ROOT / "build"
    if build_dir.exists():
        shutil.rmtree(build_dir, ignore_errors=True)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()

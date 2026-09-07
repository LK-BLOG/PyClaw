#!/usr/bin/env python3
"""
PyClaw NSIS 安装包构建器
========================
调用 NSIS makensis 编译 installer.nsi，产出 PyClaw-for-Windows-Setup.exe。
敏感/非项目文件的排除由 installer.nsi 内部的 File /r /x 完成。

用法:
  python build_installer.py
可配置:
  --makensis   makensis.exe 完整路径（默认自动探测）
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def find_makensis():
    for cand in [
        os.environ.get("NSIS_HOME", "") + r"\makensis.exe",
        r"D:\NSIS\makensis.exe",
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\NSIS\makensis.exe",
        "makensis",
    ]:
        if cand == "makensis":
            import shutil
            if shutil.which(cand):
                return cand
        elif Path(cand).exists():
            return cand
    return None


def build(makensis: str):
    nsi = ROOT / "installer.nsi"
    out = ROOT / "PyClaw-for-Windows-Setup.exe"
    print("[1/2] Compiling NSI: " + nsi.name)
    r = subprocess.run([makensis, nsi.name], cwd=ROOT, capture_output=True, text=True)
    print(r.stdout)
    if r.returncode != 0:
        print("[ERROR] makensis compile failed:")
        print(r.stderr or r.stdout)
        return False
    if out.exists():
        print(f"[2/2] Generated: {out} ({out.stat().st_size // 1024} KB)")
        return True
    print("[ERROR] output exe not found")
    return False


def main():
    args = sys.argv[1:]
    makensis = None
    if "--makensis" in args:
        makensis = args[args.index("--makensis") + 1]
    if not makensis:
        makensis = find_makensis()
    if not makensis:
        print("[ERROR] makensis.exe not found; install NSIS or pass --makensis")
        sys.exit(1)
    print("Using makensis: " + makensis)
    sys.exit(0 if build(makensis) else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
安装后引导脚本：由 NSIS 安装完毕后调用
  - 安装 Python 依赖（核心 + 可选 Skill）
  - 注册 pyclaw CLI（pip install -e .）
  - 生成 pyclaw.cmd 快捷命令，并把安装目录加入用户 PATH
"""
import os
import re
import subprocess
import sys
from pathlib import Path

if sys.platform == "win32":
    for _s in (sys.stdout, sys.stderr):
        try:
            _s.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

ROOT = Path(__file__).resolve().parent
MIRROR = ["-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]

CORE = [
    "httpx>=0.27.0", "pytz>=2024.1", "fastapi>=0.110.0",
    "uvicorn>=0.29.0", "websockets>=12.0", "python-multipart>=0.0.9",
]
OPTIONAL = [
    "pywebview>=5.0", "psutil>=5.9.0", "aiosqlite>=0.20.0",
    "python-pptx>=0.6.0", "bilibili-api-python>=1.5.0",
]


def run(args, timeout=900):
    print("   > " + " ".join(args), flush=True)
    return subprocess.run(args, capture_output=True, text=True, timeout=timeout)


def pip_install(pkgs):
    attempts = []
    base = [sys.executable, "-m", "pip", "install"]
    attempts.append(base + pkgs + MIRROR)
    attempts.append(base + ["--user"] + pkgs + MIRROR)
    attempts.append(base + ["--break-system-packages"] + pkgs + MIRROR)
    last = ""
    for args in attempts:
        try:
            p = run(args)
            if p.returncode == 0:
                return True, ""
            last = (p.stderr or p.stdout or "")[-500:]
        except Exception as e:
            last = str(e)
    return False, last


def add_to_path(put_dir):
    """把安装目录加入用户 PATH（HKCU\\Environment）。"""
    path = os.environ.get("PATH", "")
    existing = [p.strip().strip('"') for p in path.split(";") if p.strip()]
    if str(put_dir).lower() not in [p.lower() for p in existing]:
        new_path = path.rstrip(";") + ";" + str(put_dir)
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            winreg.CloseKey(key)
            os.environ["PATH"] = new_path
            return True
        except Exception:
            pass
    return False


def make_shim(put_dir):
    """生成 pyclaw.cmd，让安装目录内可运行 pyclaw <command>。"""
    cmd = put_dir / "pyclaw.cmd"
    if sys.platform == "win32":
        py = str(put_dir / "python_portable" / "python.exe") if (put_dir / "python_portable" / "python.exe").exists() else "python"
        content = f'@echo off\r\n"{py}" "{put_dir}\\pyclaw\\cli.py" %*\r\n'
    else:
        content = f'#!/usr/bin/env bash\nexec "{ROOT}/启动.sh" "$@"\n'
    try:
        cmd.write_text(content, encoding="utf-8")
        if sys.platform != "win32":
            os.chmod(cmd, 0o755)
        return True
    except Exception:
        return False


def main():
    print("=== PyClaw 安装后引导 ===", flush=True)
    print("[1/3] 安装核心依赖...", flush=True)
    ok, err = pip_install(CORE)
    if not ok:
        print(f"[WARN] 核心依赖安装失败: {err}", flush=True)
    else:
        print("[OK] 核心依赖完成", flush=True)

    print("[2/3] 安装可选依赖 (Skill/Desktop)...", flush=True)
    ok, err = pip_install(OPTIONAL)
    print("[OK] 可选依赖处理完成", flush=True)

    print("[3/3] 注册 pyclaw CLI...", flush=True)
    ok, err = pip_install(["-e", str(ROOT)])
    shim = make_shim(ROOT)
    path_ok = add_to_path(ROOT)
    print("[OK] CLI 注册完成" if ok else f"[WARN] CLI 注册失败: {err}", flush=True)
    if shim:
        print(f"[OK] 已生成快捷命令: {ROOT / 'pyclaw.cmd'}", flush=True)
    if path_ok:
        print("[OK] 已把安装目录加入用户 PATH", flush=True)
    print("=== 引导结束，可重新打开终端使用 pyclaw ===", flush=True)


if __name__ == "__main__":
    main()

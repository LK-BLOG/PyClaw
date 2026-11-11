#!/usr/bin/env python3
"""PyClaw 环境自检。

用法：双击「诊断.bat」，或者在这个目录执行：

    python check_env.py

它会告诉你：
  - 现在的 python 到底是哪一个（完整路径）
  - 依赖装没装、能不能 import
  - 如果缺，该用哪条命令装（命令里带的就是上面这个 python）
"""
import importlib
import os
import sys

MODULES = [
    ("openai", "openai>=1.0.0"),
    ("fastapi", "fastapi>=0.110.0"),
    ("uvicorn", "uvicorn>=0.29.0"),
    ("websockets", "websockets>=12.0"),
    ("httpx", "httpx>=0.27.0"),
    ("pydantic", "pydantic>=2.0"),
    ("prompt_toolkit", "prompt_toolkit>=3.0.0"),
    ("rich", "rich>=13.0.0"),
    ("pytz", "pytz>=2024.1"),
    ("multipart", "python-multipart>=0.0.9"),
]


def main():
    print("=" * 62)
    print(" PyClaw 环境自检")
    print("=" * 62)
    print(f" Python      : {sys.version.split()[0]}")
    print(f" 解释器路径  : {sys.executable}")
    print(f" 工作目录    : {os.getcwd()}")
    print(f" 系统        : {sys.platform}")
    print("-" * 62)

    missing = []
    for name, pkg in MODULES:
        try:
            mod = importlib.import_module(name)
            ver = getattr(mod, "__version__", "") or ""
            print(f" [OK]   {pkg:<28} {ver}")
        except Exception as exc:
            print(f" [缺失] {pkg:<28} {type(exc).__name__}: {exc}")
            missing.append(pkg)

    print("-" * 62)
    if missing:
        print(" 有依赖没装上。这台机器上可能装了多个 Python，")
        print(" pip 装到了另一个，而 PyClaw 用的是上面那个解释器。")
        print("")
        print(" 直接执行这条（用的是上面那个 python）：")
        print("")
        print('   "%s" -m pip install %s' % (sys.executable, " ".join(missing)))
        print("")
        print(" 如果提示权限不足，加 --user：")
        print("")
        print('   "%s" -m pip install --user %s' % (sys.executable, " ".join(missing)))
    else:
        print(" 依赖齐全，可以直接启动：")
        print('   "%s" webapp.py' % sys.executable)

    print("-" * 62)
    print(" sys.path:")
    for p in sys.path:
        if p:
            print("   " + p)
    print("=" * 62)
    return 0 if not missing else 1


if __name__ == "__main__":
    try:
        code = main()
    except Exception as exc:
        print("自检炸了：%r" % (exc,))
        code = 2
    if sys.platform == "win32":
        try:
            input("\n按回车关闭…")
        except Exception:
            pass
    sys.exit(code)

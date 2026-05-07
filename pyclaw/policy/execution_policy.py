import re
from enum import Enum


class RiskLevel(Enum):
    SAFE = "safe"
    TOOL = "tool"
    SYSTEM = "system"


class PolicyResult:
    def __init__(self, allow: bool, risk_level: RiskLevel, reason: str = "", require_confirm: bool = False):
        self.allow = allow
        self.risk_level = risk_level
        self.reason = reason
        self.require_confirm = require_confirm

    def __repr__(self):
        return f"PolicyResult(allow={self.allow}, risk={self.risk_level.value}, confirm={self.require_confirm}, reason='{self.reason}')"


# 危险命令正则 - 直接拦截，永不放行
DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",                    # 删除根目录
    r"rm\s+-rf\s+~",                    # 删除home
    r"shutdown\s*(-h|-r)?",             # 关机
    r"reboot",                          # 重启
    r"mkfs",                            # 格式化
    r":\(\)\{\s*:\|\:&\s*\}",           # fork炸弹
    r"dd\s+if=",                        # 磁盘写
    r"chmod\s+-R\s+777",                # 全权限递归
    r"wget\s+.*\|\s*bash",              # 管道执行
    r"curl\s+.*\|\s*bash",              # 管道执行
    r">\s*/dev/sd",                     # 写裸设备
]


# pip白名单 - 这些可以直接装，其他需要用户确认
ALLOWED_PIP = {
    "requests",
    "numpy",
    "pydantic",
    "pyyaml",
    "python-dotenv",
    "rich",
    "click",
    "httpx",
    "aiohttp",
    "jinja2",
}


# Python危险用法 - 拦截直接系统调用
PYTHON_DANGEROUS = [
    "os.system",
    "subprocess.run",
    "subprocess.call",
    "subprocess.Popen",
    "exec(",
    "eval(",
    "__import__('os')",
    "__import__('subprocess')",
]


class ExecutionPolicy:
    """PyClaw执行策略层 - 所有执行必须先过这里"""

    def check_bash(self, cmd: str) -> PolicyResult:
        """检查bash命令"""
        # 先拦致命危险命令
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                return PolicyResult(
                    allow=False,
                    risk_level=RiskLevel.SYSTEM,
                    reason=f"致命危险命令已拦截: {pattern}"
                )

        # sudo直接拦（系统级）
        if "sudo" in cmd.lower() or "doas" in cmd.lower():
            return PolicyResult(
                allow=False,
                risk_level=RiskLevel.SYSTEM,
                reason="sudo/doas 需要用户手动确认",
                require_confirm=True
            )

        # 普通bash命令归为TOOL级
        return PolicyResult(
            allow=True,
            risk_level=RiskLevel.TOOL,
            reason="bash命令允许执行"
        )

    def check_pip(self, package: str) -> PolicyResult:
        """检查pip安装"""
        # 提取包名（去掉版本号）
        pkg_name = package.split("==")[0].split(">=")[0].split("<=")[0].strip()

        if pkg_name in ALLOWED_PIP:
            return PolicyResult(
                allow=True,
                risk_level=RiskLevel.TOOL,
                reason=f"包 {pkg_name} 在白名单中"
            )

        return PolicyResult(
            allow=False,
            risk_level=RiskLevel.SYSTEM,
            reason=f"包 {pkg_name} 不在白名单",
            require_confirm=True
        )

    def check_python(self, code: str) -> PolicyResult:
        """检查Python代码"""
        for dangerous in PYTHON_DANGEROUS:
            if dangerous in code:
                return PolicyResult(
                    allow=False,
                    risk_level=RiskLevel.SYSTEM,
                    reason=f"拦截不安全Python用法: {dangerous}",
                    require_confirm=True
                )

        return PolicyResult(
            allow=True,
            risk_level=RiskLevel.TOOL,
            reason="Python代码安全"
        )

    def check_file(self, action: str, path: str) -> PolicyResult:
        """检查文件操作"""
        # 只读操作全是SAFE
        if action in ["read", "list_dir", "stat"]:
            return PolicyResult(
                allow=True,
                risk_level=RiskLevel.SAFE,
                reason=f"文件只读操作: {action}"
            )

        # 写操作是TOOL
        if action in ["write", "edit", "delete", "mkdir"]:
            return PolicyResult(
                allow=True,
                risk_level=RiskLevel.TOOL,
                reason=f"文件写操作: {action}"
            )

        return PolicyResult(
            allow=False,
            risk_level=RiskLevel.SYSTEM,
            reason=f"未知文件操作: {action}"
        )

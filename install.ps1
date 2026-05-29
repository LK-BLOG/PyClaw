<#
🦞 PyClaw 一键安装脚本 (Windows PowerShell)
用法:
  本地: .\install.ps1
  远程: iwr -useb https://raw.githubusercontent.com/LK-BLOG/PyClaw/main/install.ps1 | iex
#>

$Host.UI.RawUI.WindowTitle = "PyClaw 一键安装"

Write-Host ""
Write-Host "   ╔══════════════════════════════╗" -ForegroundColor Cyan
Write-Host "   ║     🦞 PyClaw 一键安装      ║" -ForegroundColor Cyan
Write-Host "   ╚══════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── 检测 Python ──
$python = $null
foreach ($cmd in @("python3", "python")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "(\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 8) {
                $python = $cmd
                Write-Host "  ✅ Python $major.$minor+" -ForegroundColor Green
                break
            }
        }
    } catch {}
}

if (-not $python) {
    Write-Host "  ❌ 需要 Python 3.8+，请先安装:" -ForegroundColor Red
    Write-Host "     https://www.python.org/downloads/"
    Write-Host "     安装时记得勾选 'Add Python to PATH'"
    exit 1
}

# ── 确认安装目录 ──
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$inTempDir = $projectDir -match "Temp|tmp"

if ($inTempDir -or $projectDir -eq $env:USERPROFILE) {
    # 远程安装模式，需要下载
    Write-Host "  📦 下载 PyClaw..." -ForegroundColor DarkGray
    $tmpDir = Join-Path $env:TEMP "pyclaw-install"
    Remove-Item -Recurse -Force $tmpDir -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

    # 尝试 git
    try {
        git clone --depth 1 "https://github.com/LK-BLOG/PyClaw.git" $tmpDir 2>&1 | Out-Null
    } catch {}

    # git 失败回退到 curl
    if (-not (Test-Path (Join-Path $tmpDir "pyclaw"))) {
        Write-Host "  ⏳ 使用 curl 下载..." -ForegroundColor DarkGray
        $tarPath = Join-Path $env:TEMP "pyclaw.tar.gz"
        Invoke-WebRequest -Uri "https://api.github.com/repos/LK-BLOG/PyClaw/tarball/main" -OutFile $tarPath
        # PowerShell 7+ 有 tar
        tar -xzf $tarPath -C $tmpDir --strip-components=1 2>$null
        # 如果 tar 失败（Windows PowerShell），从 zip 下载
        if (-not (Test-Path (Join-Path $tmpDir "pyclaw"))) {
            $zipPath = Join-Path $env:TEMP "pyclaw.zip"
            Invoke-WebRequest -Uri "https://github.com/LK-BLOG/PyClaw/archive/refs/heads/main.zip" -OutFile $zipPath
            Expand-Archive -Path $zipPath -DestinationPath $tmpDir -Force
            $extractedDir = Join-Path $tmpDir "PyClaw-main"
            if (Test-Path $extractedDir) {
                Get-ChildItem $extractedDir | Move-Item -Destination $tmpDir
                Remove-Item -Recurse -Force $extractedDir
            }
        }
    }
    $projectDir = $tmpDir
    Write-Host "  ✅ 下载完成" -ForegroundColor Green
}

Set-Location $projectDir

# ── 询问是否安装 CLI ──
Write-Host ""
Write-Host "  🔧 是否安装 pyclaw 命令行工具?" -ForegroundColor Cyan
Write-Host "     安装后可在终端直接运行 pyclaw <command>" -ForegroundColor DarkGray
Write-Host "     不安装则需 python -m pyclaw.cli <command>" -ForegroundColor DarkGray
Write-Host ""
$installCli = Read-Host "  安装 CLI? (Y/n)"
if ($installCli -eq "" -or $installCli -eq "y" -or $installCli -eq "Y") {

# ── 安装 pyclaw CLI ──
Write-Host "  🔧 安装 pyclaw 命令..." -ForegroundColor DarkGray
$pipOk = $false
try {
    & $python -m pip install -e $projectDir --break-system-packages 2>&1 | Out-Null
    $pipOk = $true
} catch {}

if (-not $pipOk) {
    try {
        & $python -m pip install -e $projectDir 2>&1 | Out-Null
        $pipOk = $true
    } catch {}
}

if ($pipOk) {
    Write-Host "  ✅ pyclaw 命令已安装" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  pip 安装失败，使用脚本模式" -ForegroundColor Yellow
    # 创建 bat 包装
    $batContent = "@echo off`npushd %~dp0`npython -m pyclaw.cli %*`npopd"
    $batPath = Join-Path $projectDir "pyclaw.bat"
    Set-Content -Path $batPath -Value $batContent -Encoding ASCII
    Write-Host "  使用: .\pyclaw.bat <command>" -ForegroundColor DarkGray
}
} else {
    Write-Host "  ⏭️  跳过 CLI 安装" -ForegroundColor Yellow
}

# ── 安装依赖 ──
Write-Host "  📦 安装 Python 依赖..." -ForegroundColor DarkGray
try {
    & $python -m pip install httpx uvicorn fastapi websockets 2>&1 | Out-Null
} catch {}

# ── 配置向导 ──
$apiTxt = Join-Path $projectDir "API.txt"
if (Test-Path $apiTxt) {
    Write-Host "  📄 已有配置，跳过" -ForegroundColor DarkGray
} else {
    Write-Host ""
    Write-Host "  🧞 打开配置向导..." -ForegroundColor Cyan
    try {
        & $python -m pyclaw.cli setup
    } catch {
        Write-Host ""
        Write-Host "  ⚠️  配置向导异常，稍后手动运行: pyclaw setup" -ForegroundColor Yellow
    }
}

# ── 完成 ──
Write-Host ""
Write-Host "   ╔══════════════════════════════╗" -ForegroundColor Green
Write-Host "   ║     🦞 PyClaw 安装完成!      ║" -ForegroundColor Green
Write-Host "   ╚══════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  启动: pyclaw start" -ForegroundColor Cyan
Write-Host "  交互: pyclaw shell" -ForegroundColor Cyan
Write-Host ""
Pause

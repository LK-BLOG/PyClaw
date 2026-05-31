<#
🦞 PyClaw One-Click Install (Windows PowerShell)
Usage:
  Local: .\install.ps1
  Remote: iwr -useb https://raw.githubusercontent.com/LK-BLOG/PyClaw/main/install.ps1 | iex
#>

$Host.UI.RawUI.WindowTitle = "PyClaw Installer"

Write-Host ""
Write-Host "   ╔══════════════════════════════╗" -ForegroundColor Cyan
Write-Host "   ║     🦞 PyClaw Installer     ║" -ForegroundColor Cyan
Write-Host "   ╚══════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── 语言选择 ──
Write-Host ""
Write-Host "  Language / 语言" -ForegroundColor Cyan
Write-Host "    1) English"
Write-Host "    2) 中文"
Write-Host ""
$langChoice = Read-Host "  Choose (1/2)"
if ($langChoice -eq "2") {
    # 中文
    $MSG_PYTHON_OK = "检测到"
    $MSG_PYTHON_REQ = "需要 Python 3.8+，请先安装"
    $MSG_DOWNLOADING = "正在下载 PyClaw..."
    $MSG_DOWNLOAD_OK = "下载完成"
    $MSG_CLI_PROMPT = "是否安装 pyclaw 命令行工具?"
    $MSG_CLI_INSTALLED = "安装后可在终端直接运行 pyclaw <command>"
    $MSG_CLI_SKIPPED = "不安装则需 python -m pyclaw.cli <command>"
    $MSG_CLI_ASK = "安装 CLI? (Y/n)"
    $MSG_CLI_INSTALL = "正在安装 pyclaw 命令..."
    $MSG_CLI_OK = "pyclaw 命令已安装"
    $MSG_CLI_SKIP = "跳过 CLI 安装"
    $MSG_PIP_FAIL = "pip 安装失败，回退到脚本:"
    $MSG_PIP_CMD = "使用"
    $MSG_DEPS = "正在安装 Python 依赖..."
    $MSG_CFG_EXIST = "已有配置，跳过"
    $MSG_WIZARD = "打开配置向导..."
    $MSG_READY = "安装完成!"
    $MSG_START = "启动"
    $MSG_CMDS = "命令"
    $MSG_SHORTCUT_CREATE = "创建桌面快捷方式"
    $MSG_SHORTCUT_DESC = "一键启动: 开启服务 + 打开浏览器"
    $MSG_SHORTCUT_ASK = "创建快捷方式"
    $MSG_SHORTCUT_OK = "桌面快捷方式已创建!"
    $MSG_SHORTCUT_SKIP = "跳过创建桌面快捷方式"
    $MSG_SKILL_PROMPT = "选择不需要的 Skill（输入编号，逗号分隔）"
    $MSG_SKILL_HELP = "被选中的 Skill 将被禁用（移入回收站）"
    $MSG_SKILL_DONE = "Skill 配置完成"
    $MSG_SKILL_SKIP = "跳过 Skill 配置"
    $LANG_CONF = "zh-CN"
} else {
    # English
    $MSG_PYTHON_OK = "detected"
    $MSG_PYTHON_REQ = "Python 3.8+ required. Please install"
    $MSG_DOWNLOADING = "Downloading PyClaw..."
    $MSG_DOWNLOAD_OK = "Download complete"
    $MSG_CLI_PROMPT = "Install pyclaw CLI?"
    $MSG_CLI_INSTALLED = "Installed: run 'pyclaw <command>' anywhere"
    $MSG_CLI_SKIPPED = "Skipped: use 'python -m pyclaw.cli <command>' instead"
    $MSG_CLI_ASK = "Install CLI? (Y/n)"
    $MSG_CLI_INSTALL = "Installing pyclaw command..."
    $MSG_CLI_OK = "pyclaw command installed"
    $MSG_CLI_SKIP = "Skipped CLI install"
    $MSG_PIP_FAIL = "pip install failed, fallback to script:"
    $MSG_PIP_CMD = "Use"
    $MSG_DEPS = "Installing Python dependencies..."
    $MSG_CFG_EXIST = "Config already exists, skipping"
    $MSG_WIZARD = "Launching setup wizard..."
    $MSG_READY = "Ready!"
    $MSG_START = "Start"
    $MSG_CMDS = "Commands"
    $MSG_SHORTCUT_CREATE = "Create desktop shortcut"
    $MSG_SHORTCUT_DESC = "One-click launch: starts server + opens browser"
    $MSG_SHORTCUT_ASK = "Create shortcut"
    $MSG_SHORTCUT_OK = "Desktop shortcut created!"
    $MSG_SHORTCUT_SKIP = "Skipped desktop shortcut"
    $MSG_SKILL_PROMPT = "Select Skills to disable (enter numbers, comma separated)"
    $MSG_SKILL_HELP = "Selected skills will be moved to trash"
    $MSG_SKILL_DONE = "Skills configured"
    $MSG_SKILL_SKIP = "Skipped skill configuration"
    $LANG_CONF = "en-US"
}

Write-Host ""

# ── Check Python ──
$python = $null
foreach ($cmd in @("python3", "python")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "(\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 8) {
                $python = $cmd
                Write-Host "  ✅ Python $major.$minor+ $MSG_PYTHON_OK" -ForegroundColor Green
                break
            }
        }
    } catch {}
}

if (-not $python) {
    Write-Host "  ❌ $MSG_PYTHON_REQ:" -ForegroundColor Red
    Write-Host "     https://www.python.org/downloads/"
    exit 1
}

# ── Determine install directory ──
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$inTempDir = $projectDir -match "Temp|tmp"

if ($inTempDir -or $projectDir -eq $env:USERPROFILE) {
    Write-Host "  📦 $MSG_DOWNLOADING" -ForegroundColor DarkGray
    $tmpDir = Join-Path $env:TEMP "pyclaw-install"
    Remove-Item -Recurse -Force $tmpDir -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

    try {
        git clone --depth 1 "https://github.com/LK-BLOG/PyClaw.git" $tmpDir 2>&1 | Out-Null
    } catch {}

    if (-not (Test-Path (Join-Path $tmpDir "pyclaw"))) {
        Write-Host "  ⏳ Downloading via curl..." -ForegroundColor DarkGray
        $tarPath = Join-Path $env:TEMP "pyclaw.tar.gz"
        Invoke-WebRequest -Uri "https://api.github.com/repos/LK-BLOG/PyClaw/tarball/main" -OutFile $tarPath
        tar -xzf $tarPath -C $tmpDir --strip-components=1 2>$null
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
    Write-Host "  ✅ $MSG_DOWNLOAD_OK" -ForegroundColor Green
}

Set-Location $projectDir

Write-Host ""
Write-Host "  🔧 $MSG_CLI_PROMPT" -ForegroundColor Cyan
Write-Host "     $MSG_CLI_INSTALLED" -ForegroundColor DarkGray
Write-Host "     $MSG_CLI_SKIPPED" -ForegroundColor DarkGray
Write-Host ""
$installCli = Read-Host "  $($MSG_CLI_ASK):"
if ($installCli -eq "" -or $installCli -eq "y" -or $installCli -eq "Y") {

Write-Host "  🔧 $MSG_CLI_INSTALL" -ForegroundColor DarkGray
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
    Write-Host "  ✅ $MSG_CLI_OK" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  $MSG_PIP_FAIL" -ForegroundColor Yellow
    $batContent = "@echo off`npushd %~dp0`npython -m pyclaw.cli %*`npopd"
    $batPath = Join-Path $projectDir "pyclaw.bat"
    Set-Content -Path $batPath -Value $batContent -Encoding ASCII
    Write-Host "     $MSG_PIP_CMD: .\pyclaw.bat <command>" -ForegroundColor DarkGray
}
} else {
    Write-Host "  ⏭️  $MSG_CLI_SKIP" -ForegroundColor Yellow
}

Write-Host "  📦 $MSG_DEPS" -ForegroundColor DarkGray
try {
    & $python -m pip install httpx uvicorn fastapi websockets prompt_toolkit 2>&1 | Out-Null
} catch {}

Write-Host ""
Write-Host "  📌 $MSG_SHORTCUT_CREATE" -ForegroundColor Cyan
Write-Host "     $MSG_SHORTCUT_DESC" -ForegroundColor DarkGray
Write-Host ""
$createShortcut = Read-Host "  $($MSG_SHORTCUT_ASK):"
if ($createShortcut -eq "" -or $createShortcut -eq "y" -or $createShortcut -eq "Y") {
    $shortcutPath = Join-Path $env:USERPROFILE "Desktop\PyClaw.lnk"
    $wsh = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut($shortcutPath)
    $shortcut.TargetPath = Join-Path $projectDir "start.bat"
    $shortcut.WorkingDirectory = $projectDir
    $shortcut.Save()
    Write-Host "  ✅ $MSG_SHORTCUT_OK" -ForegroundColor Green
} else {
    Write-Host "  ⏭️  $MSG_SHORTCUT_SKIP" -ForegroundColor Yellow
}

$apiTxt = Join-Path $projectDir "API.txt"
if (Test-Path $apiTxt) {
    $content = Get-Content $apiTxt -Raw
    if ($content -notmatch "LANGUAGE=") {
        Add-Content -Path $apiTxt -Value "`nLANGUAGE=$LANG_CONF"
    }
} else {
    Set-Content -Path $apiTxt -Value "LANGUAGE=$LANG_CONF"
}

if (Test-Path $apiTxt) {
    $hasKey = Select-String -Path $apiTxt -Pattern "API_KEY=" -SimpleMatch -Quiet
    if ($hasKey) {
        

# ── Skill configuration ──
$skillDir = Join-Path $projectDir "skills"
$trashDir = Join-Path $skillDir ".trash"

$activeSkills = @()
if (Test-Path $skillDir) {
    Get-ChildItem $skillDir -Directory | ForEach-Object {
        $initPy = Join-Path $_.FullName "__init__.py"
        if (($_.Name -ne ".trash") -and ($_.Name -ne "__pycache__") -and (Test-Path $initPy)) {
            $activeSkills += $_.Name
        }
    }
}

if ($activeSkills.Count -gt 0) {
    Write-Host ""
    Write-Host "  🧩 $MSG_SKILL_PROMPT" -ForegroundColor Cyan
    Write-Host "     $MSG_SKILL_HELP" -ForegroundColor DarkGray
    Write-Host ""
    for ($i = 0; $i -lt $activeSkills.Count; $i++) {
        Write-Host "     $($i+1)) $($activeSkills[$i])"
    }
    Write-Host ""
    $skillChoice = Read-Host "  Numbers (comma-separated, empty=keep all)"
    if ($skillChoice -ne "") {
        New-Item -ItemType Directory -Force -Path $trashDir | Out-Null
        $selected = $skillChoice -split ","
        foreach ($sel in $selected) {
            $sel = $sel.Trim()
            $idx = [int]$sel - 1
            if ($idx -ge 0 -and $idx -lt $activeSkills.Count) {
                $skillName = $activeSkills[$idx]
                $src = Join-Path $skillDir $skillName
                $dst = Join-Path $trashDir $skillName
                Move-Item -Path $src -Destination $dst -Force
                Write-Host "  🗑️  $skillName" -ForegroundColor Yellow
            }
        }
        Write-Host "  ✅ $MSG_SKILL_DONE" -ForegroundColor Green
    } else {
        Write-Host "  ⏭️  $MSG_SKILL_SKIP" -ForegroundColor Yellow
    }
}
`nWrite-Host "  📄 $MSG_CFG_EXIST" -ForegroundColor DarkGray
    } else {
        Write-Host ""
        Write-Host "  🧞 $MSG_WIZARD" -ForegroundColor Cyan
        try {
            & $python -m pyclaw.cli setup
        } catch {
            Write-Host ""
            Write-Host "  ⚠️  Setup wizard failed" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host ""
    Write-Host "  🧞 $MSG_WIZARD" -ForegroundColor Cyan
    try {
        & $python -m pyclaw.cli setup
    } catch {
        Write-Host ""
        Write-Host "  ⚠️  Setup wizard failed" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "   ╔══════════════════════════════╗" -ForegroundColor Green
Write-Host "   ║     🦞 PyClaw $MSG_READY      ║" -ForegroundColor Green
Write-Host "   ╚══════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "   $MSG_START: pyclaw start" -ForegroundColor Cyan
Write-Host "   $MSG_CMDS:   pyclaw shell" -ForegroundColor Cyan
Write-Host ""
Pause

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
                Write-Host "  ✅ Python $major.$minor+ detected" -ForegroundColor Green
                break
            }
        }
    } catch {}
}

if (-not $python) {
    Write-Host "  ❌ Python 3.8+ required. Please install:" -ForegroundColor Red
    Write-Host "     https://www.python.org/downloads/"
    Write-Host "     Make sure to check 'Add Python to PATH'"
    exit 1
}

# ── Determine install directory ──
$projectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$inTempDir = $projectDir -match "Temp|tmp"

if ($inTempDir -or $projectDir -eq $env:USERPROFILE) {
    # Remote install mode — download from GitHub
    Write-Host "  📦 Downloading PyClaw..." -ForegroundColor DarkGray
    $tmpDir = Join-Path $env:TEMP "pyclaw-install"
    Remove-Item -Recurse -Force $tmpDir -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $tmpDir | Out-Null

    # Try git first
    try {
        git clone --depth 1 "https://github.com/LK-BLOG/PyClaw.git" $tmpDir 2>&1 | Out-Null
    } catch {}

    # Fallback to curl
    if (-not (Test-Path (Join-Path $tmpDir "pyclaw"))) {
        Write-Host "  ⏳ Downloading via curl..." -ForegroundColor DarkGray
        $tarPath = Join-Path $env:TEMP "pyclaw.tar.gz"
        Invoke-WebRequest -Uri "https://api.github.com/repos/LK-BLOG/PyClaw/tarball/main" -OutFile $tarPath
        # PowerShell 7+ has tar built-in
        tar -xzf $tarPath -C $tmpDir --strip-components=1 2>$null
        # Fallback to zip (Windows PowerShell)
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
    Write-Host "  ✅ Download complete" -ForegroundColor Green
}

Set-Location $projectDir

# ── Prompt: install CLI? ──
Write-Host ""
Write-Host "  🔧 Install pyclaw CLI?" -ForegroundColor Cyan
Write-Host "     Installed: run 'pyclaw <command>' anywhere" -ForegroundColor DarkGray
Write-Host "     Skipped:  use 'python -m pyclaw.cli <command>' instead" -ForegroundColor DarkGray
Write-Host ""
$installCli = Read-Host "  Install CLI? (Y/n)"
if ($installCli -eq "" -or $installCli -eq "y" -or $installCli -eq "Y") {

# ── Install pyclaw CLI ──
Write-Host "  🔧 Installing pyclaw command..." -ForegroundColor DarkGray
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
    Write-Host "  ✅ pyclaw command installed" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  pip install failed, fallback to script:" -ForegroundColor Yellow
    $batContent = "@echo off`npushd %~dp0`npython -m pyclaw.cli %*`npopd"
    $batPath = Join-Path $projectDir "pyclaw.bat"
    Set-Content -Path $batPath -Value $batContent -Encoding ASCII
    Write-Host "     Use: .\pyclaw.bat <command>" -ForegroundColor DarkGray
}
} else {
    Write-Host "  ⏭️  Skipped CLI install" -ForegroundColor Yellow
}

# ── Install dependencies ──
Write-Host "  📦 Installing Python dependencies..." -ForegroundColor DarkGray
try {
    & $python -m pip install httpx uvicorn fastapi websockets 2>&1 | Out-Null
} catch {}

# ── Configuration wizard ──
$apiTxt = Join-Path $projectDir "API.txt"
if (Test-Path $apiTxt) {
    Write-Host "  📄 Config already exists, skipping" -ForegroundColor DarkGray
} else {
    Write-Host ""
    Write-Host "  🧞 Launching setup wizard..." -ForegroundColor Cyan
    try {
        & $python -m pyclaw.cli setup
    } catch {
        Write-Host ""
        Write-Host "  ⚠️  Setup wizard failed, run manually: pyclaw setup" -ForegroundColor Yellow
    }
}

# ── Done ──
Write-Host ""
Write-Host "   ╔══════════════════════════════╗" -ForegroundColor Green
Write-Host "   ║     🦞 PyClaw Ready!        ║" -ForegroundColor Green
Write-Host "   ╚══════════════════════════════╝" -ForegroundColor Green
Write-Host ""
Write-Host "  Start:  pyclaw start" -ForegroundColor Cyan
Write-Host "  Chat:   pyclaw shell" -ForegroundColor Cyan
Write-Host "  Setup:  pyclaw setup" -ForegroundColor Cyan
Write-Host ""
Pause

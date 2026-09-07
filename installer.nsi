; PyClaw AI Assistant - NSIS One-Click Installer
; 保留设计：默认安装到 D:\PyClaw-for-Win，快捷方式指向 start.sh（配合 Git Bash）

Name "PyClaw AI 助手"
OutFile "PyClaw-for-Windows-Setup.exe"
InstallDir "D:\PyClaw-for-Win"
RequestExecutionLevel admin
ShowInstDetails show
ShowUnInstDetails show

Var STARTMENU_FOLDER

; 界面图标
!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

; 现代 UI（注意：不要引用不存在的 banner.bmp / welcome.bmp，否则编译失败）
!include "MUI2.nsh"

; 安装页面
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_STARTMENU Application $STARTMENU_FOLDER
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; 卸载页面
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; 语言
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "English"

; ==============================================
; 安装部分
; ==============================================

Section "PyClaw AI 助手 (必需)" SecMain
    SectionIn RO
    SetOutPath $INSTDIR

    ; 整包拷贝：从项目根打包，用 /x 排除敏感/非项目文件
    File /r \
        /x ".git" /x ".codex" /x ".claude" /x ".sessions" /x ".pytest_cache" \
        /x ".pyclaw_webview" /x ".learnings" /x "__pycache__" \
        /x "pyclaw_data" /x "pyclaw.egg-info" /x "*.egg-info" \
        /x "build" /x "dist" /x "venv" /x "python_portable" \
        /x "workspace" /x "wiki" /x "tests" /x "docs" /x ".idea" /x ".vscode" \
        /x "pyclaw.json" /x "pyclaw.local.json" /x "API.txt" /x "volc_api.txt" \
        /x ".env" /x "pyclaw_memory.db" /x ".pyclaw_desktop.log" \
        /x "*Cookie.txt" /x "*.key" /x "*.pem" /x "*.p12" /x "*.pfx" /x "*.jks" \
        /x "*.pyc" /x "*.pyo" /x "*.db" /x "*.log" /x "*.pptx" /x "*.pid" \
        /x "uninstall.exe" /x "PyClaw-for-Windows-Setup.exe" \
        /x "installer.nsi" /x "build_installer.py" \
        "*.*"

    ; 桌面快捷方式 -> start.sh（Git Bash 可执行）
    CreateShortcut "$DESKTOP\PyClaw for Windows.lnk" \
        "$INSTDIR\start.sh" "" "$INSTDIR\icon.ico" 0 SW_SHOWNORMAL

    ; 开始菜单快捷方式
    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
        CreateShortcut "$SMPROGRAMS\$STARTMENU_FOLDER\PyClaw for Windows.lnk" \
            "$INSTDIR\start.sh" "" "$INSTDIR\icon.ico"
        CreateShortcut "$SMPROGRAMS\$STARTMENU_FOLDER\卸载 PyClaw.lnk" \
            "$INSTDIR\uninstall.exe"
    !insertmacro MUI_STARTMENU_WRITE_END

    ; 写入卸载程序
    WriteUninstaller "$INSTDIR\uninstall.exe"

    ; 自动安装 Python 依赖 + 注册 pyclaw CLI（通过 Git Bash 的 bash）
    ; 找不到 bash 时静默跳过，不影响主安装
    StrCpy $0 "$INSTDIR\runtime_install.sh"
    nsExec::Exec 'bash.exe "$INSTDIR\runtime_install.sh"'

    ; 注册到添加/删除程序
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyClaw" \
        "DisplayName" "PyClaw AI 助手"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyClaw" \
        "DisplayVersion" "1.0.0"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyClaw" \
        "Publisher" "OpenClaw"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyClaw" \
        "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyClaw" \
        "InstallLocation" "$INSTDIR"
SectionEnd

; 可选：创建快速启动快捷方式
Section "创建快速启动快捷方式" SecQuickLaunch
    CreateShortcut "$QUICKLAUNCH\PyClaw for Windows.lnk" \
        "$INSTDIR\start.sh" "" "$INSTDIR\icon.ico"
SectionEnd

; ==============================================
; 卸载部分
; ==============================================

Section "Uninstall"
    !insertmacro MUI_STARTMENU_GETFOLDER Application $R0
    Delete "$SMPROGRAMS\$R0\PyClaw for Windows.lnk"
    Delete "$SMPROGRAMS\$R0\卸载 PyClaw.lnk"
    RMDir "$SMPROGRAMS\$R0"

    Delete "$DESKTOP\PyClaw for Windows.lnk"
    Delete "$QUICKLAUNCH\PyClaw for Windows.lnk"

    RMDir /r "$INSTDIR"

    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyClaw"
SectionEnd

; ==============================================
; 安装完成后
; ==============================================

Function .onInstSuccess
    MessageBox MB_YESNO|MB_ICONQUESTION \
        "安装完成！$\r$\n$\r$\n是否立即启动 PyClaw AI 助手？" \
        /SD IDYES IDYES launch IDNO noLaunch

    launch:
        ExecShell "" "$INSTDIR\start.sh"
    noLaunch:
FunctionEnd

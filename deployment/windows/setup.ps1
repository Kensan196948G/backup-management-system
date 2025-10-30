#Requires -RunAsAdministrator

<#
.SYNOPSIS
    3-2-1-1-0 Backup Management System - Windows本番環境セットアップスクリプト

.DESCRIPTION
    Windows Server環境でのシステムセットアップを自動化します。
    Python環境、ディレクトリ構造、データベース初期化を実行します。

.PARAMETER InstallPath
    インストール先ディレクトリ（デフォルト: C:\BackupSystem）

.PARAMETER PythonPath
    Python実行ファイルのパス（デフォルト: 自動検出）

.EXAMPLE
    .\setup.ps1
    .\setup.ps1 -InstallPath "D:\BackupSystem"
    .\setup.ps1 -PythonPath "C:\Python311\python.exe"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$InstallPath = "C:\BackupSystem",

    [Parameter(Mandatory=$false)]
    [string]$PythonPath = ""
)

# エラー発生時に停止
$ErrorActionPreference = "Stop"

# ログファイル設定
$LogFile = Join-Path $env:TEMP "backup_system_setup_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "[$Timestamp] [$Level] $Message"
    Write-Host $LogMessage
    Add-Content -Path $LogFile -Value $LogMessage
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Find-Python {
    Write-Log "Pythonインストールを検索中..."

    # 既に指定されている場合
    if ($PythonPath -and (Test-Path $PythonPath)) {
        return $PythonPath
    }

    # 環境変数PATHから検索
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return $pythonCmd.Source
    }

    # 一般的なインストール場所を検索
    $commonPaths = @(
        "C:\Python311\python.exe",
        "C:\Python312\python.exe",
        "C:\Program Files\Python311\python.exe",
        "C:\Program Files\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
    )

    foreach ($path in $commonPaths) {
        if (Test-Path $path) {
            return $path
        }
    }

    throw "Pythonが見つかりません。Python 3.11以上をインストールしてください。"
}

function Test-PythonVersion {
    param([string]$PythonExe)

    Write-Log "Pythonバージョンを確認中..."
    $versionOutput = & $PythonExe --version 2>&1
    Write-Log "検出されたバージョン: $versionOutput"

    if ($versionOutput -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]

        if ($major -ge 3 -and $minor -ge 11) {
            Write-Log "Pythonバージョン要件を満たしています" "INFO"
            return $true
        }
    }

    throw "Python 3.11以上が必要です。現在: $versionOutput"
}

function New-DirectoryStructure {
    Write-Log "ディレクトリ構造を作成中..."

    $directories = @(
        $InstallPath,
        "$InstallPath\data",
        "$InstallPath\logs",
        "$InstallPath\reports",
        "$InstallPath\venv"
    )

    foreach ($dir in $directories) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Log "作成: $dir"
        } else {
            Write-Log "既存: $dir"
        }
    }
}

function Copy-ApplicationFiles {
    Write-Log "アプリケーションファイルをコピー中..."

    $currentDir = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

    # コピーするディレクトリとファイル
    $items = @(
        @{Source="app"; Type="Directory"},
        @{Source="scripts"; Type="Directory"},
        @{Source="migrations"; Type="Directory"},
        @{Source="run.py"; Type="File"},
        @{Source="requirements.txt"; Type="File"},
        @{Source=".env.example"; Type="File"}
    )

    foreach ($item in $items) {
        $sourcePath = Join-Path $currentDir $item.Source
        $destPath = Join-Path $InstallPath $item.Source

        if (Test-Path $sourcePath) {
            if ($item.Type -eq "Directory") {
                if (-not (Test-Path $destPath)) {
                    New-Item -ItemType Directory -Path $destPath -Force | Out-Null
                }
                Copy-Item -Path "$sourcePath\*" -Destination $destPath -Recurse -Force
            } else {
                Copy-Item -Path $sourcePath -Destination $destPath -Force
            }
            Write-Log "コピー完了: $($item.Source)"
        } else {
            Write-Log "警告: ソースが見つかりません: $sourcePath" "WARNING"
        }
    }
}

function New-VirtualEnvironment {
    param([string]$PythonExe)

    Write-Log "Python仮想環境を作成中..."

    $venvPath = Join-Path $InstallPath "venv"

    if (Test-Path $venvPath) {
        Write-Log "既存の仮想環境を削除中..."
        Remove-Item -Path $venvPath -Recurse -Force
    }

    & $PythonExe -m venv $venvPath
    if ($LASTEXITCODE -ne 0) {
        throw "仮想環境の作成に失敗しました"
    }

    Write-Log "仮想環境作成完了: $venvPath"
}

function Install-Dependencies {
    Write-Log "依存パッケージをインストール中..."

    $venvPython = Join-Path $InstallPath "venv\Scripts\python.exe"
    $venvPip = Join-Path $InstallPath "venv\Scripts\pip.exe"
    $requirementsFile = Join-Path $InstallPath "requirements.txt"

    # pipをアップグレード
    Write-Log "pipをアップグレード中..."
    & $venvPip install --upgrade pip

    # 依存パッケージインストール
    if (Test-Path $requirementsFile) {
        Write-Log "requirements.txtからインストール中..."
        & $venvPip install -r $requirementsFile

        if ($LASTEXITCODE -ne 0) {
            throw "依存パッケージのインストールに失敗しました"
        }

        Write-Log "依存パッケージインストール完了"
    } else {
        throw "requirements.txtが見つかりません: $requirementsFile"
    }
}

function Initialize-Database {
    Write-Log "データベースを初期化中..."

    $venvPython = Join-Path $InstallPath "venv\Scripts\python.exe"
    $initScript = Join-Path $InstallPath "scripts\init_db.py"

    if (-not (Test-Path $initScript)) {
        Write-Log "警告: init_db.pyが見つかりません" "WARNING"
        return
    }

    Push-Location $InstallPath
    try {
        & $venvPython $initScript

        if ($LASTEXITCODE -eq 0) {
            Write-Log "データベース初期化完了"
        } else {
            Write-Log "データベース初期化中にエラーが発生しました" "WARNING"
        }
    } finally {
        Pop-Location
    }
}

function New-AdminUser {
    Write-Log "管理者ユーザーを作成中..."

    $venvPython = Join-Path $InstallPath "venv\Scripts\python.exe"
    $createAdminScript = Join-Path $InstallPath "scripts\create_admin.py"

    if (-not (Test-Path $createAdminScript)) {
        Write-Log "警告: create_admin.pyが見つかりません" "WARNING"
        return
    }

    # 管理者情報を入力
    Write-Host "`n=== 管理者ユーザー作成 ===" -ForegroundColor Cyan
    $adminUsername = Read-Host "管理者ユーザー名 (デフォルト: admin)"
    if ([string]::IsNullOrWhiteSpace($adminUsername)) {
        $adminUsername = "admin"
    }

    $adminEmail = Read-Host "管理者メールアドレス (デフォルト: admin@example.com)"
    if ([string]::IsNullOrWhiteSpace($adminEmail)) {
        $adminEmail = "admin@example.com"
    }

    $adminPassword = Read-Host "管理者パスワード" -AsSecureString
    $adminPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($adminPassword)
    )

    Push-Location $InstallPath
    try {
        & $venvPython $createAdminScript --username $adminUsername --email $adminEmail --password $adminPasswordPlain

        if ($LASTEXITCODE -eq 0) {
            Write-Log "管理者ユーザー作成完了: $adminUsername"
        } else {
            Write-Log "管理者ユーザー作成中にエラーが発生しました" "WARNING"
        }
    } finally {
        Pop-Location
    }
}

function New-EnvironmentFile {
    Write-Log "環境設定ファイルを作成中..."

    $envFile = Join-Path $InstallPath ".env"
    $envExample = Join-Path $InstallPath ".env.example"

    if (Test-Path $envFile) {
        Write-Log ".envファイルが既に存在します"
        $overwrite = Read-Host ".envファイルを上書きしますか? (y/N)"
        if ($overwrite -ne "y" -and $overwrite -ne "Y") {
            Write-Log ".envファイルのスキップ"
            return
        }
    }

    # SECRET_KEY生成
    $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 50 | ForEach-Object {[char]$_})

    # データベースパス
    $dbPath = Join-Path $InstallPath "data\backup_mgmt.db"
    $dbPath = $dbPath -replace '\\', '/'

    $envContent = @"
# Flask環境設定
FLASK_ENV=production
SECRET_KEY=$secretKey
DATABASE_URL=sqlite:///$dbPath

# メール設定（必要に応じて設定）
# MAIL_SERVER=smtp.example.com
# MAIL_PORT=587
# MAIL_USE_TLS=true
# MAIL_USERNAME=backup-system@example.com
# MAIL_PASSWORD=your-mail-password

# Microsoft Teams通知設定（必要に応じて設定）
# TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/your-webhook-url

# アプリケーション設定
APP_NAME=3-2-1-1-0 Backup Management System
APP_VERSION=1.0.0
"@

    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    Write-Log "環境設定ファイル作成完了: $envFile"
}

# メイン処理
try {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "3-2-1-1-0 Backup Management System" -ForegroundColor Cyan
    Write-Host "Windows本番環境セットアップ" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    Write-Log "セットアップ開始"
    Write-Log "ログファイル: $LogFile"

    # 管理者権限チェック
    if (-not (Test-Administrator)) {
        throw "このスクリプトは管理者権限で実行してください"
    }
    Write-Log "管理者権限確認: OK"

    # Python検出とバージョン確認
    $pythonExe = Find-Python
    Write-Log "Python実行ファイル: $pythonExe"
    Test-PythonVersion -PythonExe $pythonExe

    # ディレクトリ構造作成
    New-DirectoryStructure

    # アプリケーションファイルコピー
    Copy-ApplicationFiles

    # 仮想環境作成
    New-VirtualEnvironment -PythonExe $pythonExe

    # 依存パッケージインストール
    Install-Dependencies

    # 環境設定ファイル作成
    New-EnvironmentFile

    # データベース初期化
    Initialize-Database

    # 管理者ユーザー作成
    New-AdminUser

    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "セットアップ完了！" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green

    Write-Host "インストール先: $InstallPath" -ForegroundColor Yellow
    Write-Host "ログファイル: $LogFile" -ForegroundColor Yellow
    Write-Host "`n次のステップ:" -ForegroundColor Cyan
    Write-Host "  1. サービスをインストール: .\install_service.ps1" -ForegroundColor White
    Write-Host "  2. ファイアウォールを設定: .\configure_firewall.ps1" -ForegroundColor White
    Write-Host "  3. インストールを確認: .\verify_installation.ps1" -ForegroundColor White

    Write-Log "セットアップ正常終了"

} catch {
    Write-Log "エラーが発生しました: $_" "ERROR"
    Write-Host "`nエラーが発生しました: $_" -ForegroundColor Red
    Write-Host "詳細はログファイルを確認してください: $LogFile" -ForegroundColor Yellow
    exit 1
}

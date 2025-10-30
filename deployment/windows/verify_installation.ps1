#Requires -RunAsAdministrator

<#
.SYNOPSIS
    3-2-1-1-0 Backup Management System - インストール確認

.DESCRIPTION
    インストール状態とサービス稼働状況を確認します。

.PARAMETER InstallPath
    インストール先ディレクトリ（デフォルト: C:\BackupSystem）

.PARAMETER ServiceName
    サービス名（デフォルト: BackupManagementSystem）

.PARAMETER Port
    待受ポート（デフォルト: 5000）

.EXAMPLE
    .\verify_installation.ps1
    .\verify_installation.ps1 -Port 8080
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$InstallPath = "C:\BackupSystem",

    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "BackupManagementSystem",

    [Parameter(Mandatory=$false)]
    [int]$Port = 5000
)

$ErrorActionPreference = "Continue"

# 結果格納
$results = @{
    Success = 0
    Warning = 0
    Error = 0
    Checks = @()
}

function Write-Result {
    param(
        [string]$Category,
        [string]$Check,
        [string]$Status,
        [string]$Message,
        [string]$Details = ""
    )

    $statusColor = switch ($Status) {
        "OK" { "Green"; $results.Success++ }
        "WARNING" { "Yellow"; $results.Warning++ }
        "ERROR" { "Red"; $results.Error++ }
    }

    $icon = switch ($Status) {
        "OK" { "✓" }
        "WARNING" { "⚠" }
        "ERROR" { "✗" }
    }

    Write-Host "$icon [$Category] " -NoNewline -ForegroundColor $statusColor
    Write-Host "$Check" -NoNewline
    Write-Host " - $Message" -ForegroundColor $statusColor

    if ($Details) {
        Write-Host "  詳細: $Details" -ForegroundColor Gray
    }

    $results.Checks += @{
        Category = $Category
        Check = $Check
        Status = $Status
        Message = $Message
        Details = $Details
    }
}

function Test-PythonInstallation {
    Write-Host "`n=== Python環境 ===" -ForegroundColor Cyan

    # Python実行ファイル
    $pythonExe = Join-Path $InstallPath "venv\Scripts\python.exe"
    if (Test-Path $pythonExe) {
        try {
            $version = & $pythonExe --version 2>&1
            Write-Result "Python" "実行ファイル" "OK" "検出" $version
        } catch {
            Write-Result "Python" "実行ファイル" "ERROR" "実行不可" $_.Exception.Message
            return
        }
    } else {
        Write-Result "Python" "実行ファイル" "ERROR" "未検出" $pythonExe
        return
    }

    # pip
    $pipExe = Join-Path $InstallPath "venv\Scripts\pip.exe"
    if (Test-Path $pipExe) {
        Write-Result "Python" "pip" "OK" "検出" $pipExe
    } else {
        Write-Result "Python" "pip" "WARNING" "未検出" $pipExe
    }

    # 依存パッケージ
    try {
        $packages = & $pipExe list 2>&1 | Out-String
        if ($packages -match "Flask") {
            Write-Result "Python" "依存パッケージ" "OK" "インストール済み"
        } else {
            Write-Result "Python" "依存パッケージ" "WARNING" "未完全"
        }
    } catch {
        Write-Result "Python" "依存パッケージ" "ERROR" "確認失敗" $_.Exception.Message
    }
}

function Test-DirectoryStructure {
    Write-Host "`n=== ディレクトリ構造 ===" -ForegroundColor Cyan

    $directories = @(
        @{Path=""; Name="インストールルート"},
        @{Path="app"; Name="アプリケーション"},
        @{Path="scripts"; Name="スクリプト"},
        @{Path="data"; Name="データ"},
        @{Path="logs"; Name="ログ"},
        @{Path="reports"; Name="レポート"},
        @{Path="venv"; Name="仮想環境"}
    )

    foreach ($dir in $directories) {
        $fullPath = if ($dir.Path) { Join-Path $InstallPath $dir.Path } else { $InstallPath }
        if (Test-Path $fullPath) {
            Write-Result "ディレクトリ" $dir.Name "OK" "存在" $fullPath
        } else {
            Write-Result "ディレクトリ" $dir.Name "WARNING" "未存在" $fullPath
        }
    }
}

function Test-ConfigurationFiles {
    Write-Host "`n=== 設定ファイル ===" -ForegroundColor Cyan

    $files = @(
        @{Path="run.py"; Name="起動スクリプト"; Required=$true},
        @{Path=".env"; Name="環境設定"; Required=$true},
        @{Path="requirements.txt"; Name="依存関係定義"; Required=$true},
        @{Path="data\backup_mgmt.db"; Name="データベース"; Required=$true}
    )

    foreach ($file in $files) {
        $fullPath = Join-Path $InstallPath $file.Path
        if (Test-Path $fullPath) {
            $size = (Get-Item $fullPath).Length
            Write-Result "設定ファイル" $file.Name "OK" "存在" "$fullPath ($size bytes)"
        } else {
            $status = if ($file.Required) { "ERROR" } else { "WARNING" }
            Write-Result "設定ファイル" $file.Name $status "未存在" $fullPath
        }
    }
}

function Test-ServiceStatus {
    Write-Host "`n=== Windowsサービス ===" -ForegroundColor Cyan

    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        Write-Result "サービス" "登録状態" "OK" "登録済み" $ServiceName

        $status = $service.Status
        if ($status -eq 'Running') {
            Write-Result "サービス" "稼働状態" "OK" "稼働中" $status
        } else {
            Write-Result "サービス" "稼働状態" "ERROR" "停止中" $status
        }

        $startType = $service.StartType
        if ($startType -eq 'Automatic') {
            Write-Result "サービス" "自動起動" "OK" "有効" $startType
        } else {
            Write-Result "サービス" "自動起動" "WARNING" "無効" $startType
        }
    } else {
        Write-Result "サービス" "登録状態" "ERROR" "未登録" $ServiceName
    }
}

function Test-PortListening {
    Write-Host "`n=== ネットワーク ===" -ForegroundColor Cyan

    $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1

    if ($connection) {
        $process = Get-Process -Id $connection.OwningProcess -ErrorAction SilentlyContinue
        $processName = if ($process) { $process.ProcessName } else { "Unknown" }
        Write-Result "ネットワーク" "ポートリスニング" "OK" "ポート$Port でリスニング中" "プロセス: $processName (PID: $($connection.OwningProcess))"
    } else {
        Write-Result "ネットワーク" "ポートリスニング" "ERROR" "ポート$Port でリスニングされていません"
    }

    # IPアドレス表示
    $adapters = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*" } |
        Select-Object -First 5

    if ($adapters) {
        foreach ($adapter in $adapters) {
            Write-Result "ネットワーク" "IPアドレス" "OK" $adapter.IPAddress $adapter.InterfaceAlias
        }
    }
}

function Test-FirewallRules {
    Write-Host "`n=== ファイアウォール ===" -ForegroundColor Cyan

    $httpRule = Get-NetFirewallRule -DisplayName "3-2-1-1-0 Backup Management System (HTTP)" -ErrorAction SilentlyContinue
    if ($httpRule) {
        if ($httpRule.Enabled) {
            Write-Result "ファイアウォール" "HTTPルール" "OK" "有効" $httpRule.DisplayName
        } else {
            Write-Result "ファイアウォール" "HTTPルール" "WARNING" "無効" $httpRule.DisplayName
        }
    } else {
        Write-Result "ファイアウォール" "HTTPルール" "WARNING" "未設定"
    }

    $httpsRule = Get-NetFirewallRule -DisplayName "3-2-1-1-0 Backup Management System (HTTPS)" -ErrorAction SilentlyContinue
    if ($httpsRule) {
        if ($httpsRule.Enabled) {
            Write-Result "ファイアウォール" "HTTPSルール" "OK" "有効" $httpsRule.DisplayName
        } else {
            Write-Result "ファイアウォール" "HTTPSルール" "WARNING" "無効" $httpsRule.DisplayName
        }
    }
}

function Test-HTTPEndpoint {
    Write-Host "`n=== HTTPエンドポイント ===" -ForegroundColor Cyan

    # localhost
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$Port" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
        Write-Result "エンドポイント" "localhost" "OK" "接続成功 (HTTP $($response.StatusCode))"
    } catch {
        Write-Result "エンドポイント" "localhost" "ERROR" "接続失敗" $_.Exception.Message
    }

    # 外部IPアドレス
    $externalIPs = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*" } |
        Select-Object -First 1

    if ($externalIPs) {
        foreach ($adapter in $externalIPs) {
            try {
                $response = Invoke-WebRequest -Uri "http://$($adapter.IPAddress):$Port" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
                Write-Result "エンドポイント" $adapter.IPAddress "OK" "接続成功 (HTTP $($response.StatusCode))"
            } catch {
                Write-Result "エンドポイント" $adapter.IPAddress "WARNING" "接続失敗" $_.Exception.Message
            }
        }
    }
}

function Test-DatabaseConnection {
    Write-Host "`n=== データベース ===" -ForegroundColor Cyan

    $dbPath = Join-Path $InstallPath "data\backup_mgmt.db"
    if (Test-Path $dbPath) {
        $dbSize = (Get-Item $dbPath).Length
        Write-Result "データベース" "ファイル" "OK" "存在" "$dbPath ($dbSize bytes)"

        # データベース接続テスト（簡易）
        $pythonExe = Join-Path $InstallPath "venv\Scripts\python.exe"
        if (Test-Path $pythonExe) {
            $testScript = @"
import sys
import sqlite3
try:
    conn = sqlite3.connect('$($dbPath -replace '\\', '\\')')
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM sqlite_master WHERE type=\"table\"')
    count = cursor.fetchone()[0]
    print(f'テーブル数: {count}')
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f'エラー: {e}')
    sys.exit(1)
"@
            $tempScript = Join-Path $env:TEMP "db_test.py"
            Set-Content -Path $tempScript -Value $testScript

            try {
                $output = & $pythonExe $tempScript 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Result "データベース" "接続" "OK" "接続成功" $output
                } else {
                    Write-Result "データベース" "接続" "ERROR" "接続失敗" $output
                }
            } catch {
                Write-Result "データベース" "接続" "ERROR" "テスト失敗" $_.Exception.Message
            } finally {
                Remove-Item -Path $tempScript -Force -ErrorAction SilentlyContinue
            }
        }
    } else {
        Write-Result "データベース" "ファイル" "ERROR" "未存在" $dbPath
    }
}

function Test-LogFiles {
    Write-Host "`n=== ログファイル ===" -ForegroundColor Cyan

    $logFiles = @(
        "logs\app.log",
        "logs\service_stdout.log",
        "logs\service_stderr.log"
    )

    foreach ($logFile in $logFiles) {
        $logPath = Join-Path $InstallPath $logFile
        if (Test-Path $logPath) {
            $size = (Get-Item $logPath).Length
            $lastWrite = (Get-Item $logPath).LastWriteTime
            Write-Result "ログ" (Split-Path -Leaf $logFile) "OK" "存在" "$size bytes, 最終更新: $lastWrite"
        } else {
            Write-Result "ログ" (Split-Path -Leaf $logFile) "WARNING" "未存在" $logPath
        }
    }
}

function Show-Summary {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "確認結果サマリー" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    Write-Host "成功: " -NoNewline -ForegroundColor Green
    Write-Host $results.Success

    Write-Host "警告: " -NoNewline -ForegroundColor Yellow
    Write-Host $results.Warning

    Write-Host "エラー: " -NoNewline -ForegroundColor Red
    Write-Host $results.Error

    Write-Host "`n合計チェック項目: $($results.Checks.Count)" -ForegroundColor White

    # 総合判定
    if ($results.Error -eq 0 -and $results.Warning -eq 0) {
        Write-Host "`n✓ インストールは正常です！" -ForegroundColor Green
        return 0
    } elseif ($results.Error -eq 0) {
        Write-Host "`n⚠ インストールは概ね正常ですが、警告があります" -ForegroundColor Yellow
        return 1
    } else {
        Write-Host "`n✗ インストールに問題があります" -ForegroundColor Red
        return 2
    }
}

function Show-AccessInfo {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "アクセス情報" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    Write-Host "システムURL:" -ForegroundColor Yellow
    Write-Host "  http://localhost:$Port" -ForegroundColor White

    $externalIPs = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*" } |
        Select-Object -First 5

    foreach ($adapter in $externalIPs) {
        Write-Host "  http://$($adapter.IPAddress):$Port" -ForegroundColor White
    }

    Write-Host "`nデフォルトログイン:" -ForegroundColor Yellow
    Write-Host "  ユーザー名: admin" -ForegroundColor White
    Write-Host "  パスワード: (セットアップ時に設定)" -ForegroundColor White
}

# メイン処理
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "3-2-1-1-0 Backup Management System" -ForegroundColor Cyan
Write-Host "インストール確認" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 各種確認
Test-PythonInstallation
Test-DirectoryStructure
Test-ConfigurationFiles
Test-ServiceStatus
Test-PortListening
Test-FirewallRules
Test-HTTPEndpoint
Test-DatabaseConnection
Test-LogFiles

# サマリー表示
$exitCode = Show-Summary

# アクセス情報表示
if ($exitCode -eq 0) {
    Show-AccessInfo
}

Write-Host "`n========================================`n" -ForegroundColor Cyan

exit $exitCode

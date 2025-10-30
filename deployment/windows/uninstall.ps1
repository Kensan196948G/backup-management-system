#Requires -RunAsAdministrator

<#
.SYNOPSIS
    3-2-1-1-0 Backup Management System - アンインストール

.DESCRIPTION
    サービス、ファイアウォールルール、アプリケーションファイルを削除します。

.PARAMETER InstallPath
    インストール先ディレクトリ（デフォルト: C:\BackupSystem）

.PARAMETER ServiceName
    サービス名（デフォルト: BackupManagementSystem）

.PARAMETER BackupData
    データをバックアップするかどうか

.PARAMETER RemoveData
    データディレクトリも削除するかどうか（慎重に使用）

.EXAMPLE
    .\uninstall.ps1
    .\uninstall.ps1 -BackupData
    .\uninstall.ps1 -RemoveData
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$InstallPath = "C:\BackupSystem",

    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "BackupManagementSystem",

    [Parameter(Mandatory=$false)]
    [switch]$BackupData,

    [Parameter(Mandatory=$false)]
    [switch]$RemoveData
)

$ErrorActionPreference = "Stop"

$LogFile = Join-Path $env:TEMP "backup_system_uninstall_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

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

function Backup-ApplicationData {
    Write-Log "データをバックアップ中..."

    $backupDir = Join-Path $env:TEMP "BackupSystem_Backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -ItemType Directory -Path $backupDir -Force | Out-Null

    # バックアップ対象
    $itemsToBackup = @(
        @{Source="data"; Dest="data"},
        @{Source=".env"; Dest=".env"},
        @{Source="logs"; Dest="logs"}
    )

    foreach ($item in $itemsToBackup) {
        $sourcePath = Join-Path $InstallPath $item.Source
        if (Test-Path $sourcePath) {
            $destPath = Join-Path $backupDir $item.Dest

            if (Test-Path $sourcePath -PathType Container) {
                Copy-Item -Path $sourcePath -Destination $destPath -Recurse -Force
            } else {
                Copy-Item -Path $sourcePath -Destination $destPath -Force
            }

            Write-Log "バックアップ: $($item.Source)"
        }
    }

    Write-Log "バックアップ完了: $backupDir"
    Write-Host "`nバックアップ先: $backupDir" -ForegroundColor Yellow
    return $backupDir
}

function Stop-BackupService {
    Write-Log "サービスを停止中..."

    $service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
    if ($service) {
        if ($service.Status -eq 'Running') {
            Stop-Service -Name $ServiceName -Force
            Write-Log "サービス停止: $ServiceName"
            Start-Sleep -Seconds 2
        } else {
            Write-Log "サービスは既に停止しています: $($service.Status)"
        }
    } else {
        Write-Log "サービスが見つかりません: $ServiceName" "WARNING"
    }
}

function Remove-BackupService {
    Write-Log "サービスを削除中..."

    # NSSMを検索
    $nssmPaths = @(
        (Join-Path $InstallPath "nssm\nssm.exe"),
        "nssm.exe"
    )

    $nssmExe = $null
    foreach ($path in $nssmPaths) {
        if (Test-Path $path) {
            $nssmExe = $path
            break
        }
    }

    if (-not $nssmExe) {
        $nssmCmd = Get-Command nssm -ErrorAction SilentlyContinue
        if ($nssmCmd) {
            $nssmExe = $nssmCmd.Source
        }
    }

    if ($nssmExe) {
        Write-Log "NSSM使用: $nssmExe"
        & $nssmExe remove $ServiceName confirm
        if ($LASTEXITCODE -eq 0) {
            Write-Log "サービス削除成功: $ServiceName"
        } else {
            Write-Log "サービス削除時に警告が発生しました" "WARNING"
        }
    } else {
        Write-Log "NSSMが見つかりません。sc.exeで削除を試みます" "WARNING"
        & sc.exe delete $ServiceName
    }

    Start-Sleep -Seconds 2
}

function Remove-FirewallRules {
    Write-Log "ファイアウォールルールを削除中..."

    $ruleNames = @(
        "3-2-1-1-0 Backup Management System (HTTP)",
        "3-2-1-1-0 Backup Management System (HTTPS)"
    )

    foreach ($ruleName in $ruleNames) {
        $rule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        if ($rule) {
            Remove-NetFirewallRule -DisplayName $ruleName
            Write-Log "ファイアウォールルール削除: $ruleName"
        }
    }
}

function Remove-ApplicationFiles {
    Write-Log "アプリケーションファイルを削除中..."

    if (Test-Path $InstallPath) {
        if ($RemoveData) {
            Write-Log "全ファイル削除中（データ含む）..."
            Remove-Item -Path $InstallPath -Recurse -Force
            Write-Log "削除完了: $InstallPath"
        } else {
            Write-Log "データを除くファイルを削除中..."

            # 削除対象（dataディレクトリは保持）
            $itemsToRemove = @(
                "app",
                "scripts",
                "migrations",
                "venv",
                "nssm",
                "run.py",
                "requirements.txt",
                ".env.example"
            )

            foreach ($item in $itemsToRemove) {
                $itemPath = Join-Path $InstallPath $item
                if (Test-Path $itemPath) {
                    Remove-Item -Path $itemPath -Recurse -Force
                    Write-Log "削除: $item"
                }
            }

            Write-Log "データディレクトリは保持されました: $(Join-Path $InstallPath 'data')"
        }
    } else {
        Write-Log "インストールパスが見つかりません: $InstallPath" "WARNING"
    }
}

# メイン処理
try {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "3-2-1-1-0 Backup Management System" -ForegroundColor Cyan
    Write-Host "アンインストール" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    Write-Log "アンインストール開始"
    Write-Log "ログファイル: $LogFile"

    # 管理者権限チェック
    if (-not (Test-Administrator)) {
        throw "このスクリプトは管理者権限で実行してください"
    }
    Write-Log "管理者権限確認: OK"

    # 確認
    Write-Host "以下の操作を実行します:" -ForegroundColor Yellow
    Write-Host "  - サービスの停止と削除: $ServiceName" -ForegroundColor White
    Write-Host "  - ファイアウォールルールの削除" -ForegroundColor White
    if ($RemoveData) {
        Write-Host "  - 全ファイルの削除（データ含む）: $InstallPath" -ForegroundColor Red
    } else {
        Write-Host "  - アプリケーションファイルの削除（データは保持）: $InstallPath" -ForegroundColor White
    }
    if ($BackupData) {
        Write-Host "  - データのバックアップ" -ForegroundColor White
    }

    Write-Host ""
    $confirm = Read-Host "続行しますか? (yes/no)"
    if ($confirm -ne "yes") {
        Write-Log "アンインストールをキャンセルしました"
        Write-Host "アンインストールをキャンセルしました" -ForegroundColor Yellow
        exit 0
    }

    # データバックアップ
    $backupPath = $null
    if ($BackupData -and (Test-Path $InstallPath)) {
        $backupPath = Backup-ApplicationData
    }

    # サービス停止
    Stop-BackupService

    # サービス削除
    Remove-BackupService

    # ファイアウォールルール削除
    Remove-FirewallRules

    # アプリケーションファイル削除
    Remove-ApplicationFiles

    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "アンインストール完了！" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green

    Write-Host "削除内容:" -ForegroundColor Yellow
    Write-Host "  - サービス: $ServiceName" -ForegroundColor White
    Write-Host "  - ファイアウォールルール" -ForegroundColor White

    if ($RemoveData) {
        Write-Host "  - 全ファイル: $InstallPath" -ForegroundColor White
    } else {
        Write-Host "  - アプリケーションファイル" -ForegroundColor White
        if (Test-Path (Join-Path $InstallPath "data")) {
            Write-Host "`nデータディレクトリは保持されました:" -ForegroundColor Cyan
            Write-Host "  $(Join-Path $InstallPath 'data')" -ForegroundColor White
        }
    }

    if ($backupPath) {
        Write-Host "`nバックアップ:" -ForegroundColor Cyan
        Write-Host "  $backupPath" -ForegroundColor White
    }

    Write-Host "`nログファイル:" -ForegroundColor Cyan
    Write-Host "  $LogFile" -ForegroundColor White

    Write-Log "アンインストール正常終了"

} catch {
    Write-Log "エラーが発生しました: $_" "ERROR"
    Write-Host "`nエラーが発生しました: $_" -ForegroundColor Red
    Write-Host "詳細はログファイルを確認してください: $LogFile" -ForegroundColor Yellow
    exit 1
}

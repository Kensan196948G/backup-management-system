#Requires -RunAsAdministrator

<#
.SYNOPSIS
    3-2-1-1-0 Backup Management System - Windowsサービスインストール

.DESCRIPTION
    NSSMを使用してWindowsサービスとして登録します。

.PARAMETER InstallPath
    インストール先ディレクトリ（デフォルト: C:\BackupSystem）

.PARAMETER ServiceName
    サービス名（デフォルト: BackupManagementSystem）

.PARAMETER Port
    待受ポート（デフォルト: 5000）

.EXAMPLE
    .\install_service.ps1
    .\install_service.ps1 -Port 8080
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

$ErrorActionPreference = "Stop"

$LogFile = Join-Path $env:TEMP "backup_system_service_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

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

function Get-NSSM {
    Write-Log "NSSMの存在を確認中..."

    # インストールパス内のNSSMディレクトリ
    $nssmDir = Join-Path $InstallPath "nssm"
    $nssmExe = Join-Path $nssmDir "nssm.exe"

    if (Test-Path $nssmExe) {
        Write-Log "NSSM検出: $nssmExe"
        return $nssmExe
    }

    # システムPATHから検索
    $nssmCmd = Get-Command nssm -ErrorAction SilentlyContinue
    if ($nssmCmd) {
        Write-Log "NSSM検出 (PATH): $($nssmCmd.Source)"
        return $nssmCmd.Source
    }

    # NSSMをダウンロード
    Write-Log "NSSMをダウンロード中..."
    $nssmVersion = "2.24"
    $nssmUrl = "https://nssm.cc/release/nssm-$nssmVersion.zip"
    $tempZip = Join-Path $env:TEMP "nssm.zip"
    $tempExtract = Join-Path $env:TEMP "nssm_extract"

    try {
        # ダウンロード
        Write-Log "ダウンロード元: $nssmUrl"
        Invoke-WebRequest -Uri $nssmUrl -OutFile $tempZip -UseBasicParsing

        # 展開
        Write-Log "ファイルを展開中..."
        if (Test-Path $tempExtract) {
            Remove-Item -Path $tempExtract -Recurse -Force
        }
        Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force

        # アーキテクチャ判定（64bit/32bit）
        if ([Environment]::Is64BitOperatingSystem) {
            $nssmSourceExe = Get-ChildItem -Path $tempExtract -Filter "nssm.exe" -Recurse |
                Where-Object { $_.DirectoryName -match "win64" } |
                Select-Object -First 1
        } else {
            $nssmSourceExe = Get-ChildItem -Path $tempExtract -Filter "nssm.exe" -Recurse |
                Where-Object { $_.DirectoryName -match "win32" } |
                Select-Object -First 1
        }

        if (-not $nssmSourceExe) {
            throw "NSSM実行ファイルが見つかりません"
        }

        # インストールディレクトリにコピー
        if (-not (Test-Path $nssmDir)) {
            New-Item -ItemType Directory -Path $nssmDir -Force | Out-Null
        }

        Copy-Item -Path $nssmSourceExe.FullName -Destination $nssmExe -Force
        Write-Log "NSSM配置完了: $nssmExe"

        # クリーンアップ
        Remove-Item -Path $tempZip -Force -ErrorAction SilentlyContinue
        Remove-Item -Path $tempExtract -Recurse -Force -ErrorAction SilentlyContinue

        return $nssmExe

    } catch {
        Write-Log "NSSMのダウンロードに失敗しました: $_" "ERROR"
        throw
    }
}

function Test-ServiceExists {
    param([string]$Name)

    $service = Get-Service -Name $Name -ErrorAction SilentlyContinue
    return $null -ne $service
}

function Remove-ExistingService {
    param([string]$NssmExe, [string]$Name)

    Write-Log "既存のサービスを削除中..."

    # サービス停止
    $service = Get-Service -Name $Name -ErrorAction SilentlyContinue
    if ($service -and $service.Status -eq 'Running') {
        Write-Log "サービスを停止中..."
        Stop-Service -Name $Name -Force
        Start-Sleep -Seconds 2
    }

    # サービス削除
    & $NssmExe remove $Name confirm
    if ($LASTEXITCODE -eq 0) {
        Write-Log "既存のサービスを削除しました"
        Start-Sleep -Seconds 2
    } else {
        Write-Log "サービス削除時に警告が発生しました" "WARNING"
    }
}

function Install-BackupService {
    param([string]$NssmExe)

    Write-Log "サービスをインストール中..."

    $pythonExe = Join-Path $InstallPath "venv\Scripts\python.exe"
    $runScript = Join-Path $InstallPath "run.py"

    # 実行ファイルの存在確認
    if (-not (Test-Path $pythonExe)) {
        throw "Python実行ファイルが見つかりません: $pythonExe"
    }

    if (-not (Test-Path $runScript)) {
        throw "run.pyが見つかりません: $runScript"
    }

    # サービスインストール
    $arguments = "--host 0.0.0.0 --port $Port --production"
    & $NssmExe install $ServiceName $pythonExe $runScript $arguments

    if ($LASTEXITCODE -ne 0) {
        throw "サービスのインストールに失敗しました"
    }

    Write-Log "サービスインストール完了"

    # サービス設定
    Write-Log "サービス設定を適用中..."

    # 表示名
    & $NssmExe set $ServiceName DisplayName "3-2-1-1-0 Backup Management System"

    # 説明
    & $NssmExe set $ServiceName Description "Enterprise backup management system with 3-2-1-1-0 rule monitoring and reporting"

    # 作業ディレクトリ
    & $NssmExe set $ServiceName AppDirectory $InstallPath

    # 環境変数
    & $NssmExe set $ServiceName AppEnvironmentExtra "FLASK_ENV=production"

    # スタートアップタイプ（自動）
    & $NssmExe set $ServiceName Start SERVICE_AUTO_START

    # 標準出力・エラー出力のリダイレクト
    $stdoutLog = Join-Path $InstallPath "logs\service_stdout.log"
    $stderrLog = Join-Path $InstallPath "logs\service_stderr.log"
    & $NssmExe set $ServiceName AppStdout $stdoutLog
    & $NssmExe set $ServiceName AppStderr $stderrLog

    # ログローテーション設定
    & $NssmExe set $ServiceName AppStdoutCreationDisposition 4
    & $NssmExe set $ServiceName AppStderrCreationDisposition 4
    & $NssmExe set $ServiceName AppRotateFiles 1
    & $NssmExe set $ServiceName AppRotateOnline 1
    & $NssmExe set $ServiceName AppRotateSeconds 86400
    & $NssmExe set $ServiceName AppRotateBytes 10485760

    Write-Log "サービス設定完了"
}

function Start-BackupService {
    Write-Log "サービスを起動中..."

    Start-Service -Name $ServiceName

    Start-Sleep -Seconds 3

    $service = Get-Service -Name $ServiceName
    if ($service.Status -eq 'Running') {
        Write-Log "サービス起動成功: $($service.Status)"
        return $true
    } else {
        Write-Log "サービス起動失敗: $($service.Status)" "ERROR"
        return $false
    }
}

function Test-ServiceEndpoint {
    Write-Log "エンドポイント接続テスト中..."

    Start-Sleep -Seconds 5

    try {
        $response = Invoke-WebRequest -Uri "http://localhost:$Port" -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -eq 200) {
            Write-Log "エンドポイント接続成功 (HTTP $($response.StatusCode))"
            return $true
        }
    } catch {
        Write-Log "エンドポイント接続失敗: $_" "WARNING"
        return $false
    }

    return $false
}

# メイン処理
try {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "3-2-1-1-0 Backup Management System" -ForegroundColor Cyan
    Write-Host "Windowsサービスインストール" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    Write-Log "サービスインストール開始"
    Write-Log "ログファイル: $LogFile"

    # 管理者権限チェック
    if (-not (Test-Administrator)) {
        throw "このスクリプトは管理者権限で実行してください"
    }
    Write-Log "管理者権限確認: OK"

    # インストールパス確認
    if (-not (Test-Path $InstallPath)) {
        throw "インストールパスが見つかりません: $InstallPath`nsetup.ps1を先に実行してください"
    }
    Write-Log "インストールパス確認: $InstallPath"

    # NSSM取得
    $nssmExe = Get-NSSM

    # 既存サービス確認
    if (Test-ServiceExists -Name $ServiceName) {
        Write-Host "`n既存のサービスが見つかりました: $ServiceName" -ForegroundColor Yellow
        $remove = Read-Host "既存のサービスを削除して再インストールしますか? (y/N)"

        if ($remove -eq "y" -or $remove -eq "Y") {
            Remove-ExistingService -NssmExe $nssmExe -Name $ServiceName
        } else {
            Write-Log "インストールをキャンセルしました"
            exit 0
        }
    }

    # サービスインストール
    Install-BackupService -NssmExe $nssmExe

    # サービス起動
    if (Start-BackupService) {
        Write-Log "サービス起動確認: OK"

        # エンドポイントテスト
        if (Test-ServiceEndpoint) {
            Write-Log "エンドポイント確認: OK"
        } else {
            Write-Log "エンドポイント確認: 失敗（サービスは起動していますが接続できません）" "WARNING"
        }
    } else {
        throw "サービスの起動に失敗しました"
    }

    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "サービスインストール完了！" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green

    Write-Host "サービス名: $ServiceName" -ForegroundColor Yellow
    Write-Host "URL: http://localhost:$Port" -ForegroundColor Yellow
    Write-Host "URL: http://192.168.3.135:$Port" -ForegroundColor Yellow
    Write-Host "ログファイル: $LogFile" -ForegroundColor Yellow

    Write-Host "`nサービス管理コマンド:" -ForegroundColor Cyan
    Write-Host "  起動: Start-Service $ServiceName" -ForegroundColor White
    Write-Host "  停止: Stop-Service $ServiceName" -ForegroundColor White
    Write-Host "  再起動: Restart-Service $ServiceName" -ForegroundColor White
    Write-Host "  状態確認: Get-Service $ServiceName" -ForegroundColor White

    Write-Host "`n次のステップ:" -ForegroundColor Cyan
    Write-Host "  1. ファイアウォールを設定: .\configure_firewall.ps1" -ForegroundColor White
    Write-Host "  2. インストールを確認: .\verify_installation.ps1" -ForegroundColor White

    Write-Log "サービスインストール正常終了"

} catch {
    Write-Log "エラーが発生しました: $_" "ERROR"
    Write-Host "`nエラーが発生しました: $_" -ForegroundColor Red
    Write-Host "詳細はログファイルを確認してください: $LogFile" -ForegroundColor Yellow
    exit 1
}

#Requires -RunAsAdministrator

<#
.SYNOPSIS
    3-2-1-1-0 Backup Management System - Windowsファイアウォール設定

.DESCRIPTION
    必要なポートに対するファイアウォールルールを設定します。

.PARAMETER Port
    待受ポート（デフォルト: 5000）

.PARAMETER AllowedNetwork
    許可するネットワーク（デフォルト: 192.168.3.0/24）

.PARAMETER AllowHTTPS
    HTTPSポート（443）も開放するかどうか

.EXAMPLE
    .\configure_firewall.ps1
    .\configure_firewall.ps1 -Port 8080
    .\configure_firewall.ps1 -AllowedNetwork "10.0.0.0/8" -AllowHTTPS
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [int]$Port = 5000,

    [Parameter(Mandatory=$false)]
    [string]$AllowedNetwork = "192.168.3.0/24",

    [Parameter(Mandatory=$false)]
    [switch]$AllowHTTPS
)

$ErrorActionPreference = "Stop"

$LogFile = Join-Path $env:TEMP "backup_system_firewall_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

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

function Remove-ExistingRule {
    param([string]$RuleName)

    $existingRule = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue
    if ($existingRule) {
        Write-Log "既存のルールを削除中: $RuleName"
        Remove-NetFirewallRule -DisplayName $RuleName
        Write-Log "削除完了: $RuleName"
    }
}

function New-FirewallRule {
    param(
        [string]$RuleName,
        [int]$PortNumber,
        [string]$Network
    )

    Write-Log "ファイアウォールルールを作成中: $RuleName"

    # 既存ルール削除
    Remove-ExistingRule -RuleName $RuleName

    # 新規ルール作成
    New-NetFirewallRule `
        -DisplayName $RuleName `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort $PortNumber `
        -RemoteAddress $Network `
        -Action Allow `
        -Profile Domain,Private `
        -Enabled True | Out-Null

    Write-Log "ルール作成完了: $RuleName (ポート: $PortNumber, ネットワーク: $Network)"
}

function Test-FirewallRule {
    param([string]$RuleName)

    $rule = Get-NetFirewallRule -DisplayName $RuleName -ErrorAction SilentlyContinue
    if ($rule) {
        $enabled = $rule.Enabled
        Write-Log "ルール確認: $RuleName (有効: $enabled)"
        return $enabled
    }

    Write-Log "ルールが見つかりません: $RuleName" "WARNING"
    return $false
}

function Show-FirewallStatus {
    Write-Log "ファイアウォール状態を確認中..."

    $profiles = Get-NetFirewallProfile
    foreach ($profile in $profiles) {
        $status = if ($profile.Enabled) { "有効" } else { "無効" }
        Write-Log "  $($profile.Name): $status"
    }
}

function Test-PortListening {
    param([int]$PortNumber)

    Write-Log "ポート$PortNumber のリスニング状態を確認中..."

    $connection = Get-NetTCPConnection -LocalPort $PortNumber -ErrorAction SilentlyContinue |
        Where-Object { $_.State -eq 'Listen' } |
        Select-Object -First 1

    if ($connection) {
        Write-Log "ポート$PortNumber はリスニング中です (PID: $($connection.OwningProcess))"
        return $true
    } else {
        Write-Log "ポート$PortNumber はリスニングされていません" "WARNING"
        return $false
    }
}

# メイン処理
try {
    Write-Host "`n========================================" -ForegroundColor Cyan
    Write-Host "3-2-1-1-0 Backup Management System" -ForegroundColor Cyan
    Write-Host "Windowsファイアウォール設定" -ForegroundColor Cyan
    Write-Host "========================================`n" -ForegroundColor Cyan

    Write-Log "ファイアウォール設定開始"
    Write-Log "ログファイル: $LogFile"

    # 管理者権限チェック
    if (-not (Test-Administrator)) {
        throw "このスクリプトは管理者権限で実行してください"
    }
    Write-Log "管理者権限確認: OK"

    # 現在のファイアウォール状態表示
    Show-FirewallStatus

    # HTTPルール作成
    $httpRuleName = "3-2-1-1-0 Backup Management System (HTTP)"
    Write-Host "`nHTTPポートのファイアウォールルールを作成中..." -ForegroundColor Yellow
    New-FirewallRule -RuleName $httpRuleName -PortNumber $Port -Network $AllowedNetwork

    # HTTPSルール作成（オプション）
    if ($AllowHTTPS) {
        $httpsRuleName = "3-2-1-1-0 Backup Management System (HTTPS)"
        Write-Host "HTTPSポートのファイアウォールルールを作成中..." -ForegroundColor Yellow
        New-FirewallRule -RuleName $httpsRuleName -PortNumber 443 -Network $AllowedNetwork
    }

    # ルール確認
    Write-Host "`nファイアウォールルールの確認中..." -ForegroundColor Yellow
    $httpRuleOk = Test-FirewallRule -RuleName $httpRuleName

    if ($AllowHTTPS) {
        $httpsRuleOk = Test-FirewallRule -RuleName $httpsRuleName
    }

    # ポートリスニング確認
    Write-Host "`nポートリスニング状態の確認中..." -ForegroundColor Yellow
    $portListening = Test-PortListening -PortNumber $Port

    # ネットワーク情報表示
    Write-Host "`nネットワークインターフェース情報:" -ForegroundColor Cyan
    $networkAdapters = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*" } |
        Select-Object -First 5

    foreach ($adapter in $networkAdapters) {
        Write-Host "  $($adapter.IPAddress) ($($adapter.InterfaceAlias))" -ForegroundColor White
    }

    Write-Host "`n========================================" -ForegroundColor Green
    Write-Host "ファイアウォール設定完了！" -ForegroundColor Green
    Write-Host "========================================`n" -ForegroundColor Green

    Write-Host "設定内容:" -ForegroundColor Yellow
    Write-Host "  HTTPポート: $Port" -ForegroundColor White
    Write-Host "  許可ネットワーク: $AllowedNetwork" -ForegroundColor White
    if ($AllowHTTPS) {
        Write-Host "  HTTPSポート: 443" -ForegroundColor White
    }

    Write-Host "`n作成されたルール:" -ForegroundColor Cyan
    Write-Host "  - $httpRuleName" -ForegroundColor White
    if ($AllowHTTPS) {
        Write-Host "  - $httpsRuleName" -ForegroundColor White
    }

    Write-Host "`nアクセスURL:" -ForegroundColor Cyan
    foreach ($adapter in $networkAdapters) {
        Write-Host "  http://$($adapter.IPAddress):$Port" -ForegroundColor White
    }

    if (-not $portListening) {
        Write-Host "`n⚠ 警告: ポート$Port はまだリスニングされていません" -ForegroundColor Yellow
        Write-Host "サービスが起動しているか確認してください: Get-Service BackupManagementSystem" -ForegroundColor Yellow
    }

    Write-Host "`nファイアウォールルール管理コマンド:" -ForegroundColor Cyan
    Write-Host "  一覧表示: Get-NetFirewallRule -DisplayName '*Backup Management*'" -ForegroundColor White
    Write-Host "  無効化: Disable-NetFirewallRule -DisplayName '$httpRuleName'" -ForegroundColor White
    Write-Host "  有効化: Enable-NetFirewallRule -DisplayName '$httpRuleName'" -ForegroundColor White
    Write-Host "  削除: Remove-NetFirewallRule -DisplayName '$httpRuleName'" -ForegroundColor White

    Write-Host "`n次のステップ:" -ForegroundColor Cyan
    Write-Host "  1. インストールを確認: .\verify_installation.ps1" -ForegroundColor White
    Write-Host "  2. Webブラウザでアクセス: http://192.168.3.135:$Port" -ForegroundColor White

    Write-Log "ファイアウォール設定正常終了"

} catch {
    Write-Log "エラーが発生しました: $_" "ERROR"
    Write-Host "`nエラーが発生しました: $_" -ForegroundColor Red
    Write-Host "詳細はログファイルを確認してください: $LogFile" -ForegroundColor Yellow
    exit 1
}

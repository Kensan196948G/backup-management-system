#!/bin/bash

#
# アンインストールスクリプト
# 3-2-1-1-0 Backup Management System
#

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 設定
APP_DIR="/opt/backup-management-system"
APP_USER="backupmgmt"
APP_GROUP="backupmgmt"
LOG_DIR="/var/log/backup-management-system"
DATA_DIR="/var/lib/backup-management-system"

# ============================================================================
# ログ関数
# ============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1" >&2
}

# ============================================================================
# エラーハンドリング
# ============================================================================

trap 'log_error "スクリプト実行中にエラーが発生しました (行: $LINENO)"; exit 1' ERR

check_error() {
    if [ $? -ne 0 ]; then
        log_error "$1"
        exit 1
    fi
}

# ============================================================================
# 前提条件チェック
# ============================================================================

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "このスクリプトはroot権限で実行してください"
        exit 1
    fi
}

# ============================================================================
# サービス停止
# ============================================================================

stop_services() {
    log_info "サービスを停止中..."

    # backup-managementサービスの停止
    if systemctl is-active --quiet backup-management.service; then
        log_info "backup-management.serviceを停止中..."
        systemctl stop backup-management.service
        log_success "backup-management.serviceを停止しました"
    fi

    # 有効化を解除
    if systemctl is-enabled --quiet backup-management.service 2>/dev/null; then
        systemctl disable backup-management.service
        log_success "backup-management.serviceを無効化しました"
    fi

    # nginxの設定確認
    if [ -L /etc/nginx/sites-enabled/backup-management.conf ]; then
        log_info "nginxサイト設定を無効化中..."
        rm /etc/nginx/sites-enabled/backup-management.conf
        systemctl reload nginx 2>/dev/null || true
        log_success "nginxサイト設定を無効化しました"
    fi
}

# ============================================================================
# ファイル削除
# ============================================================================

remove_application_files() {
    log_info "アプリケーションファイルを削除中..."

    if [ -d "$APP_DIR" ]; then
        log_warn "ディレクトリを削除します: $APP_DIR"
        rm -rf "$APP_DIR"
        log_success "アプリケーションディレクトリを削除しました"
    fi

    if [ -d "$LOG_DIR" ]; then
        log_warn "ログディレクトリを削除します: $LOG_DIR"
        read -p "ログファイルをバックアップしますか？ (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            local backup_file="/var/log/backup-management-system-$(date '+%Y%m%d-%H%M%S').tar.gz"
            tar czf "$backup_file" "$LOG_DIR"
            log_success "ログをバックアップしました: $backup_file"
        fi
        rm -rf "$LOG_DIR"
    fi

    if [ -d "$DATA_DIR" ]; then
        log_warn "データディレクトリを削除します: $DATA_DIR"
        read -p "データベースをバックアップしますか？ (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            local backup_file="/var/lib/backup-management-system-$(date '+%Y%m%d-%H%M%S').tar.gz"
            tar czf "$backup_file" "$DATA_DIR"
            log_success "データをバックアップしました: $backup_file"
        fi
        rm -rf "$DATA_DIR"
    fi
}

# ============================================================================
# systemdユニット削除
# ============================================================================

remove_systemd_unit() {
    log_info "systemdユニットを削除中..."

    if [ -f /etc/systemd/system/backup-management.service ]; then
        rm /etc/systemd/system/backup-management.service
        systemctl daemon-reload
        log_success "systemdユニットを削除しました"
    fi
}

# ============================================================================
# ユーザー削除
# ============================================================================

remove_app_user() {
    log_info "アプリケーションユーザーを削除中..."

    if id "$APP_USER" &>/dev/null; then
        userdel "$APP_USER"
        log_success "ユーザーを削除しました: $APP_USER"
    fi
}

# ============================================================================
# nginx設定削除
# ============================================================================

remove_nginx_config() {
    log_info "nginxコンフィグを削除中..."

    if [ -f /etc/nginx/sites-available/backup-management.conf ]; then
        rm /etc/nginx/sites-available/backup-management.conf
        log_success "nginxコンフィグを削除しました"
    fi

    # デフォルトサイトを復元（必要に応じて）
    if [ ! -L /etc/nginx/sites-enabled/default ]; then
        if [ -f /etc/nginx/sites-available/default ]; then
            log_info "nginxデフォルトサイトを復元中..."
            ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default
        fi
    fi
}

# ============================================================================
# サマリー表示
# ============================================================================

show_summary() {
    log_success "=========================================="
    log_success "アンインストールが完了しました！"
    log_success "=========================================="

    cat << EOF

[削除内容]

- アプリケーションディレクトリ: $APP_DIR
- ログディレクトリ: $LOG_DIR
- データディレクトリ: $DATA_DIR
- systemdユニット: /etc/systemd/system/backup-management.service
- nginxコンフィグ: /etc/nginx/sites-available/backup-management.conf
- ユーザー: $APP_USER

[注意事項]

以下の項目は手動で削除する必要があります:

1. SSL証明書（オプション）:
   sudo certbot delete --cert-name backup.example.com

2. システムパッケージ（オプション）:
   sudo apt-get autoremove
   sudo apt-get remove python3-venv python3-pip nginx

3. 関連するシステムユーザー:
   sudo deluser $APP_GROUP

[バックアップ情報]

バックアップされたファイルがある場合は以下の場所から復元できます:
- ログバックアップ: /var/log/backup-management-system-*.tar.gz
- データバックアップ: /var/lib/backup-management-system-*.tar.gz

復元例:
sudo tar xzf /var/log/backup-management-system-*.tar.gz -C /

EOF
}

# ============================================================================
# メイン処理
# ============================================================================

main() {
    log_info "=========================================="
    log_info "アンインストールスクリプト"
    log_info "3-2-1-1-0 Backup Management System"
    log_info "=========================================="
    echo

    # 前提条件チェック
    check_root

    # アンインストール確認
    log_warn "このスクリプトはシステムからアプリケーションを完全に削除します"
    echo
    log_warn "以下のディレクトリが削除されます:"
    log_warn "  - $APP_DIR"
    log_warn "  - $LOG_DIR"
    log_warn "  - $DATA_DIR"
    echo
    read -p "本当にアンインストールしますか？ (yes/no): " -r
    if [[ ! $REPLY == "yes" ]]; then
        log_info "アンインストールを中止します"
        exit 0
    fi

    # アンインストール実行
    stop_services
    remove_nginx_config
    remove_systemd_unit
    remove_application_files
    remove_app_user

    # サマリー表示
    show_summary
}

# スクリプト実行
main

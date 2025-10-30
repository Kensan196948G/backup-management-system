#!/bin/bash

#
# メンテナンス・運用管理スクリプト
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
LOG_DIR="/var/log/backup-management-system"
DATA_DIR="/var/lib/backup-management-system"
BACKUP_DIR="/backup"

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
# 前提条件チェック
# ============================================================================

check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_error "このスクリプトはroot権限で実行してください"
        exit 1
    fi
}

# ============================================================================
# ステータス確認
# ============================================================================

show_status() {
    log_info "=========================================="
    log_info "システムステータス確認"
    log_info "=========================================="

    echo
    log_info "サービス状態:"
    systemctl status backup-management.service --no-pager

    echo
    log_info "nginx状態:"
    systemctl status nginx --no-pager

    echo
    log_info "最近のエラーログ (過去10件):"
    sudo -u $APP_USER tail -10 "$LOG_DIR/app.log" 2>/dev/null || log_warn "ログファイルが見つかりません"

    echo
    log_info "ディスク使用状況:"
    du -sh "$APP_DIR" "$LOG_DIR" "$DATA_DIR" 2>/dev/null || true

    echo
    log_info "メモリ使用状況:"
    free -h

    echo
    log_info "アップタイム:"
    uptime
}

# ============================================================================
# ログローテーション
# ============================================================================

rotate_logs() {
    log_info "ログファイルをローテーション中..."

    # 古いログを圧縮して保存
    if [ -f "$LOG_DIR/app.log" ]; then
        local backup_log="$LOG_DIR/app.log.$(date +%Y%m%d-%H%M%S)"
        mv "$LOG_DIR/app.log" "$backup_log"
        gzip "$backup_log"
        log_success "ログファイルをローテーションしました: $backup_log.gz"
    fi

    # アプリケーションにシグナルを送信（ログファイルを再作成させる）
    systemctl reload backup-management.service

    # 7日以上前のログを削除
    find "$LOG_DIR" -name "app.log.*.gz" -mtime +7 -delete
    log_success "古いログファイルを削除しました"
}

# ============================================================================
# データベースのバックアップ
# ============================================================================

backup_database() {
    log_info "データベースをバックアップ中..."

    mkdir -p "$BACKUP_DIR"

    local backup_file="$BACKUP_DIR/backup_management.db.$(date +%Y%m%d-%H%M%S).tar.gz"

    # データベースファイルをバックアップ
    tar czf "$backup_file" \
        -C /var/lib/backup-management-system \
        backup_management.db 2>/dev/null || true

    if [ -f "$backup_file" ]; then
        log_success "データベースをバックアップしました: $backup_file"

        # バックアップサイズを表示
        du -h "$backup_file"

        # 30日以上前のバックアップを削除
        find "$BACKUP_DIR" -name "backup_management.db.*.tar.gz" -mtime +30 -delete
        log_success "古いバックアップを削除しました"
    else
        log_error "バックアップに失敗しました"
    fi
}

# ============================================================================
# ダータベース最適化
# ============================================================================

optimize_database() {
    log_info "データベースを最適化中..."

    cd "$APP_DIR"
    source venv/bin/activate

    python3 << 'PYTHON_EOF'
import sqlite3
import os

db_path = '/var/lib/backup-management-system/backup_management.db'

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # VACUUMコマンドを実行（ファイルサイズを圧縮）
        cursor.execute('VACUUM')
        conn.commit()

        # テーブル統計を分析
        cursor.execute('ANALYZE')
        conn.commit()

        print(f"[SUCCESS] データベース最適化完了: {db_path}")

        conn.close()
    except Exception as e:
        print(f"[ERROR] データベース最適化に失敗: {e}")
else:
    print(f"[WARN] データベースが見つかりません: {db_path}")
PYTHON_EOF
}

# ============================================================================
# SSL証明書の確認
# ============================================================================

check_ssl_certificate() {
    log_info "SSL証明書を確認中..."

    if command -v certbot &> /dev/null; then
        certbot certificates

        echo
        log_info "証明書の有効期限を確認中..."

        # 証明書が存在するか確認
        cert_dir="/etc/letsencrypt/live"
        if [ -d "$cert_dir" ]; then
            for domain_dir in "$cert_dir"/*; do
                if [ -f "$domain_dir/fullchain.pem" ]; then
                    domain=$(basename "$domain_dir")
                    expiry=$(openssl x509 -in "$domain_dir/fullchain.pem" -noout -enddate | cut -d= -f2)
                    expiry_epoch=$(date -d "$expiry" +%s)
                    current_epoch=$(date +%s)
                    days_left=$(( ($expiry_epoch - $current_epoch) / 86400 ))

                    if [ "$days_left" -lt 30 ]; then
                        log_warn "証明書の有効期限が迫っています: $domain (残り $days_left 日)"
                    else
                        log_success "証明書の有効期限: $domain (残り $days_left 日)"
                    fi
                fi
            done
        fi
    else
        log_warn "Certbotがインストールされていません"
    fi
}

# ============================================================================
# システムアップデート
# ============================================================================

update_system() {
    log_info "システムをアップデート中..."

    apt-get update
    log_success "パッケージリストを更新しました"

    log_info "アップデート可能なパッケージを表示:"
    apt-get upgrade --simulate | grep -E "^Inst" || log_info "アップデートはありません"

    read -p "セキュリティアップデートをインストールしますか？ (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        apt-get install -y --only-upgrade $(apt-get upgrade --simulate 2>/dev/null | grep "^Inst" | grep -i security | awk '{print $2}')
        log_success "セキュリティアップデートをインストールしました"
    fi
}

# ============================================================================
# ディスク空き容量の確認
# ============================================================================

check_disk_space() {
    log_info "ディスク空き容量を確認中..."

    echo
    log_info "全体:"
    df -h / | tail -1

    echo
    log_info "アプリケーションディレクトリ:"
    du -sh "$APP_DIR"

    echo
    log_info "ログディレクトリ:"
    du -sh "$LOG_DIR"

    echo
    log_info "データディレクトリ:"
    du -sh "$DATA_DIR"

    # 警告閾値（85%）
    disk_usage=$(df / | awk 'NR==2 {print int($5)}')
    if [ "$disk_usage" -gt 85 ]; then
        log_error "ディスク使用率が高い: ${disk_usage}%"
    fi
}

# ============================================================================
# プロセスの再起動
# ============================================================================

restart_service() {
    log_info "アプリケーションサービスを再起動中..."

    systemctl restart backup-management.service
    log_success "アプリケーションサービスを再起動しました"

    # ステータス確認
    sleep 2
    if systemctl is-active --quiet backup-management.service; then
        log_success "サービスが正常に起動しました"
    else
        log_error "サービスの起動に失敗しました"
        journalctl -u backup-management.service -n 20 --no-pager
    fi
}

# ============================================================================
# セキュリティチェック
# ============================================================================

security_check() {
    log_info "セキュリティチェック実行中..."

    echo
    log_info "ファイアウォール設定:"
    ufw status || log_info "UFWが有効ではありません"

    echo
    log_info "開放中のポート:"
    netstat -tulpn 2>/dev/null | grep LISTEN || log_info "netstatコマンドが見つかりません"

    echo
    log_info "SSHログイン試行:"
    grep "Failed password" /var/log/auth.log 2>/dev/null | tail -5 || log_info "ログが見つかりません"

    echo
    log_info "Fail2Banステータス:"
    systemctl status fail2ban --no-pager 2>/dev/null || log_info "Fail2Banがインストールされていません"
}

# ============================================================================
# ヘルスチェック
# ============================================================================

health_check() {
    log_info "ヘルスチェック実行中..."

    # HTTPでのヘルスチェック
    echo
    log_info "ローカルヘルスチェック (HTTP):"
    if curl -s http://127.0.0.1:5000/health > /dev/null 2>&1; then
        log_success "アプリケーション: OK"
    else
        log_error "アプリケーション: NG"
    fi

    echo
    log_info "nginxチェック:"
    if systemctl is-active --quiet nginx; then
        log_success "nginx: OK"
    else
        log_error "nginx: NG"
    fi

    echo
    log_info "データベースチェック:"
    if [ -f "$DATA_DIR/backup_management.db" ]; then
        log_success "データベースファイル: OK"
    else
        log_error "データベースファイル: NG"
    fi
}

# ============================================================================
# パフォーマンス分析
# ============================================================================

performance_analysis() {
    log_info "パフォーマンス分析中..."

    echo
    log_info "プロセスメモリ使用量:"
    ps aux | grep "[b]ackup-management" | awk '{print "  PID: " $2 ", メモリ: " $6 "KB, CPU: " $3 "%"}'

    echo
    log_info "スローログクエリ:"
    if [ -f "$LOG_DIR/app.log" ]; then
        grep "took.*ms" "$LOG_DIR/app.log" 2>/dev/null | tail -5 || log_info "スローログが見つかりません"
    fi

    echo
    log_info "アクティブなコネクション:"
    netstat -an | grep ESTABLISHED | grep 5000 | wc -l

    echo
    log_info "nginxのアクセス数（過去1時間）:"
    find /var/log/nginx -name "*access.log*" -exec grep -h "$(date -d '1 hour ago' '+%d/%b/%Y:%H')" {} \; 2>/dev/null | wc -l || log_info "ログが見つかりません"
}

# ============================================================================
# クリーンアップ
# ============================================================================

cleanup_old_files() {
    log_info "古いファイルをクリーンアップ中..."

    # 古いログを削除
    find "$LOG_DIR" -name "*.log" -mtime +30 -delete
    log_success "30日以上前のログファイルを削除しました"

    # 古いバックアップを削除
    if [ -d "$BACKUP_DIR" ]; then
        find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
        log_success "30日以上前のバックアップを削除しました"
    fi

    # 一時ファイルをクリーンアップ
    rm -rf "$APP_DIR/.pytest_cache" 2>/dev/null || true
    rm -rf "$APP_DIR/__pycache__" 2>/dev/null || true

    log_success "クリーンアップが完了しました"
}

# ============================================================================
# レポート生成
# ============================================================================

generate_report() {
    local report_file="/tmp/backup-management-system-report-$(date +%Y%m%d-%H%M%S).txt"

    log_info "レポートを生成中..."

    cat > "$report_file" << EOF
===========================================
3-2-1-1-0 Backup Management System
システムレポート
===========================================

生成日時: $(date)

[システム情報]
OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d= -f2 | tr -d '"')
カーネル: $(uname -r)
アップタイム: $(uptime -p)

[サービス状態]
EOF

    systemctl status backup-management.service --no-pager >> "$report_file" 2>&1 || true
    echo "" >> "$report_file"

    cat >> "$report_file" << EOF
[ディスク使用状況]
EOF

    df -h >> "$report_file"
    echo "" >> "$report_file"

    cat >> "$report_file" << EOF
[メモリ使用状況]
EOF

    free -h >> "$report_file"
    echo "" >> "$report_file"

    cat >> "$report_file" << EOF
[最近のエラーログ]
EOF

    tail -20 "$LOG_DIR/app.log" >> "$report_file" 2>/dev/null || echo "ログが見つかりません" >> "$report_file"

    log_success "レポートを生成しました: $report_file"
    echo "$report_file"
}

# ============================================================================
# メニュー
# ============================================================================

show_menu() {
    cat << EOF

========================================
メンテナンス・運用管理メニュー
========================================

1. ステータス確認
2. ログローテーション
3. データベースバックアップ
4. データベース最適化
5. SSL証明書確認
6. システムアップデート
7. ディスク空き容量確認
8. サービス再起動
9. セキュリティチェック
10. ヘルスチェック
11. パフォーマンス分析
12. 古いファイルをクリーンアップ
13. レポート生成
0. 終了

========================================
EOF
    read -p "選択してください (0-13): " choice
}

# ============================================================================
# メイン処理
# ============================================================================

main() {
    check_root

    while true; do
        show_menu

        case $choice in
            1) show_status ;;
            2) rotate_logs ;;
            3) backup_database ;;
            4) optimize_database ;;
            5) check_ssl_certificate ;;
            6) update_system ;;
            7) check_disk_space ;;
            8) restart_service ;;
            9) security_check ;;
            10) health_check ;;
            11) performance_analysis ;;
            12) cleanup_old_files ;;
            13) report=$(generate_report); echo "$report" ;;
            0) log_info "終了します"; exit 0 ;;
            *) log_error "無効な選択です" ;;
        esac

        echo
        read -p "Enterキーを押して続行..."
        clear
    done
}

# スクリプト実行
main

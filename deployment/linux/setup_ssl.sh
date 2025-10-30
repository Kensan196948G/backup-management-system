#!/bin/bash

#
# Let's Encrypt SSL証明書セットアップスクリプト
# 3-2-1-1-0 Backup Management System
#

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

check_certbot() {
    log_info "Certbotを確認中..."

    if ! command -v certbot &> /dev/null; then
        log_error "Certbotがインストールされていません"
        log_info "以下のコマンドでインストールしてください:"
        log_info "  sudo apt-get install certbot python3-certbot-nginx"
        exit 1
    fi

    log_success "Certbot がインストール済み"
}

check_nginx() {
    log_info "nginxを確認中..."

    if ! command -v nginx &> /dev/null; then
        log_error "nginxがインストールされていません"
        exit 1
    fi

    # nginxの実行確認
    if ! systemctl is-active --quiet nginx; then
        log_warn "nginxが起動していません。起動します..."
        systemctl start nginx
        check_error "nginxの起動に失敗しました"
    fi

    log_success "nginx がインストール済み・起動中"
}

# ============================================================================
# ドメイン設定
# ============================================================================

get_domain() {
    log_info "ドメイン設定を開始します"

    read -p "バックアップシステムのドメイン名を入力してください [backup.example.com]: " domain

    if [ -z "$domain" ]; then
        domain="backup.example.com"
        log_warn "デフォルトドメインを使用します: $domain"
    fi

    # ドメイン名の簡易バリデーション
    if ! [[ "$domain" =~ ^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.([a-zA-Z]{2,})$ ]]; then
        log_warn "ドメイン名が無効な可能性があります: $domain"
        read -p "このドメイン名を使用しますか？ (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            get_domain
            return
        fi
    fi

    log_success "ドメイン名: $domain"
}

get_email() {
    log_info "メールアドレス設定を開始します"

    read -p "Let's Encryptの通知用メールアドレスを入力してください: " email

    if [ -z "$email" ]; then
        log_error "メールアドレスは必須です"
        get_email
        return
    fi

    # メールアドレスの簡易バリデーション
    if ! [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        log_warn "メールアドレスが無効な可能性があります: $email"
        read -p "このメールアドレスを使用しますか？ (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            get_email
            return
        fi
    fi

    log_success "メールアドレス: $email"
}

# ============================================================================
# nginxコンフィグ更新
# ============================================================================

update_nginx_config() {
    log_info "nginxコンフィグを更新中..."

    local nginx_conf="/etc/nginx/sites-available/backup-management.conf"

    if [ ! -f "$nginx_conf" ]; then
        log_error "nginxコンフィグが見つかりません: $nginx_conf"
        log_info "セットアップスクリプトを先に実行してください"
        exit 1
    fi

    # ドメイン名を置換
    sed -i "s/backup\.example\.com/$domain/g" "$nginx_conf"

    # nginx設定テスト
    nginx -t
    check_error "nginx設定テストに失敗しました"

    # nginxリロード
    systemctl reload nginx

    log_success "nginxコンフィグを更新しました"
}

# ============================================================================
# SSL証明書取得
# ============================================================================

request_certificate() {
    log_info "Let's Encrypt SSL証明書を申請中..."

    certbot certonly \
        --agree-tos \
        --preferred-challenges http \
        --nginx \
        --non-interactive \
        -d "$domain" \
        -m "$email"

    check_error "SSL証明書の取得に失敗しました"

    log_success "SSL証明書を取得しました"
}

# ============================================================================
# SSL設定の有効化
# ============================================================================

enable_ssl_in_nginx() {
    log_info "nginxのSSL設定を有効化中..."

    local nginx_conf="/etc/nginx/sites-available/backup-management.conf"

    # SSL証明書パスのコメントを解除
    sed -i 's|# ssl_certificate|ssl_certificate|g' "$nginx_conf"
    sed -i 's|# ssl_certificate_key|ssl_certificate_key|g' "$nginx_conf"

    # 証明書パスを更新
    sed -i "s|/etc/letsencrypt/live/backup\.example\.com/fullchain\.pem|/etc/letsencrypt/live/$domain/fullchain.pem|g" "$nginx_conf"
    sed -i "s|/etc/letsencrypt/live/backup\.example\.com/privkey\.pem|/etc/letsencrypt/live/$domain/privkey.pem|g" "$nginx_conf"

    # nginx設定テスト
    nginx -t
    check_error "nginx設定テストに失敗しました"

    # nginxリロード
    systemctl reload nginx

    log_success "nginxのSSL設定を有効化しました"
}

# ============================================================================
# 自動更新設定
# ============================================================================

setup_auto_renewal() {
    log_info "証明書の自動更新を設定中..."

    # Certbotタイマーが既に存在するか確認
    if systemctl list-timers | grep -q "certbot"; then
        log_success "証明書自動更新は既に設定済みです"
        return 0
    fi

    # Systemdタイマー有効化
    systemctl enable certbot.timer
    systemctl start certbot.timer

    log_success "証明書の自動更新を設定しました"

    # 更新テスト
    log_info "証明書更新テストを実行中..."
    certbot renew --dry-run

    if [ $? -eq 0 ]; then
        log_success "証明書更新テストに成功しました"
    else
        log_warn "証明書更新テストに失敗しました"
        log_info "手動で確認してください: sudo certbot renew"
    fi
}

# ============================================================================
# セキュリティ検証
# ============================================================================

verify_ssl_configuration() {
    log_info "SSL設定を検証中..."

    # SSLテスト（オンライン）
    log_info "SSL/TLS設定をテスト中..."

    if [ -x "$(command -v openssl)" ]; then
        # 証明書情報表示
        echo
        log_info "証明書情報:"
        openssl x509 -in "/etc/letsencrypt/live/$domain/fullchain.pem" -text -noout | grep -E "(Subject:|Issuer:|Not Before:|Not After:)"
        echo
    fi

    log_success "SSL設定の検証が完了しました"
}

# ============================================================================
# サマリー表示
# ============================================================================

show_summary() {
    log_success "=========================================="
    log_success "SSL証明書の設定が完了しました！"
    log_success "=========================================="

    cat << EOF

[証明書情報]

- ドメイン: $domain
- 証明書パス: /etc/letsencrypt/live/$domain/fullchain.pem
- 秘密鍵パス: /etc/letsencrypt/live/$domain/privkey.pem
- 更新予定日: $(date -d "+90 days" '+%Y-%m-%d')

[自動更新設定]

Certbotの自動更新は以下のコマンドで管理できます:

# 自動更新の確認
sudo systemctl status certbot.timer

# 自動更新のテスト
sudo certbot renew --dry-run

# ログ確認
sudo journalctl -u certbot.service

[次のステップ]

1. ブラウザでアクセスして確認してください:
   https://$domain

2. SSLセキュリティをテストしてください:
   https://www.ssllabs.com/ssltest/

3. 証明書の有効期限を確認してください:
   sudo certbot certificates

4. 定期的にログを確認してください:
   sudo tail -f /var/log/letsencrypt/letsencrypt.log

[有用なコマンド]

# 証明書の更新テスト
sudo certbot renew --dry-run

# 証明書の強制更新
sudo certbot renew --force-renewal

# 証明書情報表示
sudo certbot certificates

# nginxの設定テスト
sudo nginx -t

# nginxのリロード
sudo systemctl reload nginx

[トラブルシューティング]

問題が発生した場合は、以下のログファイルを確認してください:

- Certbotログ: /var/log/letsencrypt/letsencrypt.log
- nginxログ: /var/log/nginx/error.log
- systemdログ: sudo journalctl -u certbot.service

EOF
}

# ============================================================================
# メイン処理
# ============================================================================

main() {
    log_info "=========================================="
    log_info "SSL証明書セットアップスクリプト"
    log_info "3-2-1-1-0 Backup Management System"
    log_info "=========================================="

    # 前提条件チェック
    check_root
    check_certbot
    check_nginx

    # ユーザー入力
    get_domain
    get_email

    # インストール確認
    echo
    log_info "以下の情報でSSL証明書を設定します:"
    log_info "  ドメイン: $domain"
    log_info "  メール: $email"
    echo
    read -p "続行しますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "セットアップを中止します"
        exit 0
    fi

    # インストール実行
    update_nginx_config
    request_certificate
    enable_ssl_in_nginx
    setup_auto_renewal
    verify_ssl_configuration

    # サマリー表示
    show_summary
}

# スクリプト実行
main

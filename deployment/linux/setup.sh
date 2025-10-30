#!/bin/bash

#
# Linux本番環境セットアップスクリプト
# 3-2-1-1-0 Backup Management System
# Ubuntu/Debian環境対応
#

set -e

# カラー定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ログレベル
LOG_LEVEL="${LOG_LEVEL:-INFO}"

# 設定
APP_DIR="/opt/backup-management-system"
APP_USER="backupmgmt"
APP_GROUP="backupmgmt"
PYTHON_VERSION="3.11"
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

check_os() {
    log_info "OS情報を確認中..."

    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS_NAME=$NAME
        OS_VERSION=$VERSION_ID

        case "$ID" in
            ubuntu|debian)
                log_success "サポート対象OS: $OS_NAME $OS_VERSION"
                ;;
            *)
                log_error "非サポートOS: $OS_NAME"
                log_info "このスクリプトはUbuntu/Debianをサポートしています"
                exit 1
                ;;
        esac
    else
        log_error "/etc/os-releaseが見つかりません"
        exit 1
    fi
}

check_python() {
    log_info "Pythonバージョンを確認中..."

    if ! command -v python3 &> /dev/null; then
        log_error "Python3がインストールされていません"
        exit 1
    fi

    python_version=$(python3 --version | awk '{print $2}')
    python_major=$(echo $python_version | cut -d. -f1)
    python_minor=$(echo $python_version | cut -d. -f2)

    if [ "$python_major" -lt 3 ] || ([ "$python_major" -eq 3 ] && [ "$python_minor" -lt 9 ]); then
        log_error "Python 3.9以上が必要です (インストール済み: $python_version)"
        exit 1
    fi

    log_success "Python $python_version がインストール済み"
}

# ============================================================================
# ディレクトリ作成
# ============================================================================

create_directories() {
    log_info "アプリケーションディレクトリを作成中..."

    if [ -d "$APP_DIR" ]; then
        log_warn "ディレクトリが既に存在します: $APP_DIR"
        read -p "既存のディレクトリを上書きしますか？ (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "セットアップを中止します"
            exit 0
        fi
    else
        mkdir -p "$APP_DIR"
        log_success "作成完了: $APP_DIR"
    fi

    # ログディレクトリ
    mkdir -p "$LOG_DIR"
    log_success "作成完了: $LOG_DIR"

    # データディレクトリ
    mkdir -p "$DATA_DIR"
    log_success "作成完了: $DATA_DIR"
}

# ============================================================================
# システムパッケージインストール
# ============================================================================

install_system_packages() {
    log_info "システムパッケージを更新・インストール中..."

    apt-get update
    check_error "aptリポジトリ更新に失敗しました"

    # 必須パッケージ
    local packages=(
        "python3-venv"
        "python3-pip"
        "python3-dev"
        "build-essential"
        "curl"
        "wget"
        "git"
        "nginx"
        "certbot"
        "python3-certbot-nginx"
        "supervisor"
        "sqlite3"
    )

    log_info "パッケージをインストール中: ${packages[@]}"

    apt-get install -y "${packages[@]}"
    check_error "パッケージインストールに失敗しました"

    log_success "システムパッケージのインストール完了"
}

# ============================================================================
# ユーザー・グループ作成
# ============================================================================

create_app_user() {
    log_info "アプリケーションユーザーを作成中..."

    if id "$APP_USER" &>/dev/null; then
        log_warn "ユーザーが既に存在します: $APP_USER"
    else
        useradd --system --no-create-home --shell /bin/false "$APP_USER"
        check_error "ユーザー作成に失敗しました: $APP_USER"
        log_success "ユーザーを作成しました: $APP_USER"
    fi
}

# ============================================================================
# アプリケーションファイルのコピー
# ============================================================================

copy_application_files() {
    log_info "アプリケーションファイルをコピー中..."

    # スクリプトがあるディレクトリから親ディレクトリを取得
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local source_dir="$(dirname $(dirname "$script_dir"))"

    if [ ! -d "$source_dir" ]; then
        log_error "ソースディレクトリが見つかりません: $source_dir"
        exit 1
    fi

    # 必要なファイルをコピー
    cp -r "$source_dir/app" "$APP_DIR/" 2>/dev/null || true
    cp -r "$source_dir/config" "$APP_DIR/" 2>/dev/null || true
    cp -r "$source_dir/migrations" "$APP_DIR/" 2>/dev/null || true
    cp "$source_dir/requirements.txt" "$APP_DIR/" 2>/dev/null || true
    cp "$source_dir/run.py" "$APP_DIR/" 2>/dev/null || true

    if [ ! -f "$APP_DIR/requirements.txt" ]; then
        log_warn "requirements.txtが見つかりません。デフォルトのテンプレートを作成します。"
        cat > "$APP_DIR/requirements.txt" << 'EOF'
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.5
python-dotenv==1.0.0
click==8.1.7
itsdangerous==2.1.2
Jinja2==3.1.2
MarkupSafe==2.1.3
SQLAlchemy==2.0.23
Werkzeug==3.0.1
EOF
    fi

    log_success "アプリケーションファイルをコピーしました"
}

# ============================================================================
# 仮想環境の作成と依存パッケージインストール
# ============================================================================

setup_virtual_environment() {
    log_info "Python仮想環境を作成中..."

    cd "$APP_DIR"

    # 既存の仮想環境を削除
    if [ -d "$APP_DIR/venv" ]; then
        log_warn "既存の仮想環境を削除します"
        rm -rf "$APP_DIR/venv"
    fi

    python3 -m venv venv
    check_error "仮想環境の作成に失敗しました"

    log_success "仮想環境を作成しました"

    # 仮想環境をアクティベート
    source venv/bin/activate

    # pipをアップグレード
    log_info "pipをアップグレード中..."
    pip install --upgrade pip setuptools wheel
    check_error "pipのアップグレードに失敗しました"

    # 依存パッケージをインストール
    log_info "依存パッケージをインストール中..."
    pip install -r requirements.txt
    check_error "依存パッケージのインストールに失敗しました"

    log_success "仮想環境のセットアップ完了"
}

# ============================================================================
# ファイルパーミッション設定
# ============================================================================

set_permissions() {
    log_info "ファイルパーミッションを設定中..."

    chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"
    chmod -R 755 "$APP_DIR"
    chmod 750 "$APP_DIR/venv"

    # ログディレクトリ
    chown -R "$APP_USER:$APP_GROUP" "$LOG_DIR"
    chmod 755 "$LOG_DIR"

    # データディレクトリ
    chown -R "$APP_USER:$APP_GROUP" "$DATA_DIR"
    chmod 755 "$DATA_DIR"

    log_success "ファイルパーミッションを設定しました"
}

# ============================================================================
# .envファイル設定
# ============================================================================

setup_env_file() {
    log_info ".envファイルを設定中..."

    local env_file="$APP_DIR/.env"

    if [ -f "$env_file" ]; then
        log_warn ".envファイルが既に存在します"
        return 0
    fi

    # 秘密鍵生成
    local secret_key=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
    local db_key=$(python3 -c 'import secrets; print(secrets.token_hex(16))')

    cat > "$env_file" << EOF
# Flask設定
FLASK_ENV=production
FLASK_APP=run.py
SECRET_KEY=$secret_key

# データベース設定
DATABASE_URL=sqlite:///$DATA_DIR/backup_management.db
DB_ENCRYPTION_KEY=$db_key

# ログ設定
LOG_LEVEL=INFO
LOG_FILE=$LOG_DIR/app.log

# バックアップ設定
BACKUP_DIR=/mnt/backups
RETENTION_DAYS=30

# メール通知設定（オプション）
MAIL_SERVER=
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=

# セキュリティ設定
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax

# API設定
API_RATE_LIMIT=1000
API_TIMEOUT=30
EOF

    chown "$APP_USER:$APP_GROUP" "$env_file"
    chmod 600 "$env_file"

    log_success ".envファイルを作成しました"
    log_info "設定値を確認・編集してください: $env_file"
}

# ============================================================================
# データベース初期化
# ============================================================================

initialize_database() {
    log_info "データベースを初期化中..."

    cd "$APP_DIR"
    source venv/bin/activate

    # Flaskアプリケーションの初期化
    if [ -f "run.py" ]; then
        python3 << 'PYTHON_EOF'
import sys
import os

# アプリケーションディレクトリを追加
sys.path.insert(0, '/opt/backup-management-system')

try:
    from app import create_app, db

    app = create_app('production')

    with app.app_context():
        # テーブルを作成
        db.create_all()
        print("[SUCCESS] データベーステーブルを作成しました")
except ImportError as e:
    print(f"[WARN] アプリケーション初期化に失敗しました: {e}")
    print("[INFO] デプロイ後に手動で実行してください: flask db upgrade")
except Exception as e:
    print(f"[WARN] データベース初期化に失敗しました: {e}")
PYTHON_EOF
    fi

    log_success "データベース初期化完了"
}

# ============================================================================
# systemdユニット登録
# ============================================================================

register_systemd_unit() {
    log_info "systemdユニットを登録中..."

    local unit_file="/etc/systemd/system/backup-management.service"
    local source_unit=$(dirname "${BASH_SOURCE[0]}")/systemd/backup-management.service

    if [ ! -f "$source_unit" ]; then
        log_warn "systemdユニットファイルが見つかりません。デフォルトのテンプレートを作成します。"
        source_unit=$(mktemp)
        cat > "$source_unit" << 'EOF'
[Unit]
Description=3-2-1-1-0 Backup Management System
After=network.target

[Service]
Type=simple
User=backupmgmt
WorkingDirectory=/opt/backup-management-system
Environment="FLASK_ENV=production"
EnvironmentFile=/opt/backup-management-system/.env
ExecStart=/opt/backup-management-system/venv/bin/python run.py --production
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    fi

    cp "$source_unit" "$unit_file"
    chmod 644 "$unit_file"

    systemctl daemon-reload
    check_error "systemdデーモンをリロードできません"

    systemctl enable backup-management.service
    check_error "systemdユニットの有効化に失敗しました"

    log_success "systemdユニットを登録しました"
}

# ============================================================================
# nginxリバースプロキシ設定
# ============================================================================

setup_nginx() {
    log_info "nginxリバースプロキシを設定中..."

    local nginx_conf="/etc/nginx/sites-available/backup-management.conf"
    local source_conf=$(dirname "${BASH_SOURCE[0]}")/nginx/backup-management.conf

    if [ ! -f "$source_conf" ]; then
        log_warn "nginxコンフィグが見つかりません。デフォルトのテンプレートを作成します。"
        source_conf=$(mktemp)
        cat > "$source_conf" << 'EOF'
upstream backup_app {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name backup.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name backup.example.com;

    # SSL証明書（Let's Encryptで取得後）
    # ssl_certificate /etc/letsencrypt/live/backup.example.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/backup.example.com/privkey.pem;

    # SSLセキュリティ設定
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # ログ設定
    access_log /var/log/nginx/backup-management-access.log;
    error_log /var/log/nginx/backup-management-error.log;

    # バッファ設定
    client_max_body_size 100M;

    location / {
        proxy_pass http://backup_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
    }

    location /static/ {
        alias /opt/backup-management-system/app/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF
    fi

    cp "$source_conf" "$nginx_conf"

    # シンボリックリンク作成
    if [ ! -L /etc/nginx/sites-enabled/backup-management.conf ]; then
        ln -s "$nginx_conf" /etc/nginx/sites-enabled/backup-management.conf
    fi

    # デフォルトサイトを無効化
    if [ -L /etc/nginx/sites-enabled/default ]; then
        rm /etc/nginx/sites-enabled/default
    fi

    # nginx設定テスト
    nginx -t
    check_error "nginx設定テストに失敗しました"

    # nginxリスタート
    systemctl restart nginx

    log_success "nginxリバースプロキシを設定しました"
    log_info "ドメイン名を設定して、SSL証明書を取得してください"
}

# ============================================================================
# ファイアウォール設定
# ============================================================================

setup_firewall() {
    log_info "ファイアウォール設定を確認中..."

    if command -v ufw &> /dev/null; then
        if ufw status | grep -q "Status: active"; then
            log_info "UFWを設定中..."
            ufw allow 22/tcp
            ufw allow 80/tcp
            ufw allow 443/tcp
            log_success "UFWを設定しました"
        fi
    else
        log_info "UFWがインストールされていません（オプション）"
    fi
}

# ============================================================================
# サマリー表示
# ============================================================================

show_summary() {
    log_success "=========================================="
    log_success "セットアップが完了しました！"
    log_success "=========================================="

    cat << EOF

[重要な次のステップ]

1. 環境変数ファイルを編集してください:
   sudo nano $APP_DIR/.env

2. SSL証明書を取得してください:
   sudo ./setup_ssl.sh

3. nginxコンフィグを編集してください:
   sudo nano /etc/nginx/sites-available/backup-management.conf
   - server_name を設定してください
   - SSL証明書パスのコメントを解除してください

4. アプリケーションを起動してください:
   sudo systemctl start backup-management.service
   sudo systemctl status backup-management.service

5. ログを確認してください:
   sudo journalctl -u backup-management.service -f
   tail -f $LOG_DIR/app.log

[インストール情報]

- アプリケーションディレクトリ: $APP_DIR
- ユーザー: $APP_USER
- ログディレクトリ: $LOG_DIR
- データディレクトリ: $DATA_DIR
- systemdユニット: backup-management.service
- nginx設定: /etc/nginx/sites-available/backup-management.conf

[有用なコマンド]

# サービス管理
sudo systemctl start backup-management.service
sudo systemctl stop backup-management.service
sudo systemctl restart backup-management.service
sudo systemctl status backup-management.service
sudo systemctl enable backup-management.service
sudo systemctl disable backup-management.service

# ログ確認
sudo journalctl -u backup-management.service -f
sudo tail -f $LOG_DIR/app.log

# nginx管理
sudo systemctl restart nginx
sudo nginx -t

# アンインストール
sudo ./uninstall.sh

EOF
}

# ============================================================================
# メイン処理
# ============================================================================

main() {
    log_info "=========================================="
    log_info "Linux本番環境セットアップスクリプト"
    log_info "3-2-1-1-0 Backup Management System"
    log_info "=========================================="

    # 前提条件チェック
    check_root
    check_os
    check_python

    # インストール確認
    read -p "インストールを開始しますか？ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "セットアップを中止します"
        exit 0
    fi

    # インストール実行
    create_directories
    install_system_packages
    create_app_user
    copy_application_files
    setup_virtual_environment
    set_permissions
    setup_env_file
    initialize_database
    register_systemd_unit
    setup_nginx
    setup_firewall

    # サマリー表示
    show_summary
}

# スクリプト実行
main

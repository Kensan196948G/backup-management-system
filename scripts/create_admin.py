#!/usr/bin/env python3
"""
管理者ユーザー作成スクリプト
Admin user creation script
"""
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click

from app import create_app, db
from app.models import User


def create_admin_user():
    """管理者ユーザーの作成"""
    app = create_app()

    with app.app_context():
        click.echo("=== 管理者ユーザー作成 ===\n")

        # 既存の管理者を確認
        existing_admin = User.query.filter_by(role="admin").first()
        if existing_admin:
            click.echo(f"⚠️  管理者ユーザーが既に存在します: {existing_admin.username}")
            if not click.confirm("新しい管理者を追加作成しますか？"):
                return

        # ユーザー情報の入力
        username = click.prompt("ユーザー名", default="admin")

        # ユーザー名の重複チェック
        if User.query.filter_by(username=username).first():
            click.echo(f'❌ ユーザー名 "{username}" は既に使用されています。')
            return

        email = click.prompt("メールアドレス")

        # メールアドレスの重複チェック
        if User.query.filter_by(email=email).first():
            click.echo(f'❌ メールアドレス "{email}" は既に使用されています。')
            return

        password = click.prompt("パスワード", hide_input=True, confirmation_prompt=True)

        # パスワードポリシーチェック
        if len(password) < 8:
            click.echo("❌ パスワードは8文字以上にしてください。")
            return

        full_name = click.prompt("氏名", default="システム管理者")
        department = click.prompt("部署", default="IT部門")

        # 管理者ユーザーの作成
        admin = User(username=username, email=email, full_name=full_name, department=department, role="admin", is_active=True)
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        click.echo("\n✅ 管理者ユーザーが作成されました！")
        click.echo(f"  ユーザー名: {admin.username}")
        click.echo(f"  メール: {admin.email}")
        click.echo(f"  役割: {admin.role}")
        click.echo("\nこのユーザーでログインできます。")


if __name__ == "__main__":
    create_admin_user()

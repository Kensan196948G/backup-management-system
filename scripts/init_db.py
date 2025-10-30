#!/usr/bin/env python3
"""
データベース初期化スクリプト
Database initialization script
"""
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import click

from app import create_app, db
from app.models import SystemSetting, User


def init_database():
    """データベースの初期化"""
    app = create_app()

    with app.app_context():
        # テーブル作成
        click.echo("データベーステーブルを作成中...")
        db.create_all()
        click.echo("✓ テーブル作成完了")

        # システム設定の初期化
        click.echo("システム設定を初期化中...")
        settings = [
            {"setting_key": "system_initialized", "setting_value": "true", "value_type": "bool", "description": "システム初期化フラグ"},
            {"setting_key": "min_copies", "setting_value": "3", "value_type": "int", "description": "3-2-1-1-0ルール: 最小コピー数"},
            {
                "setting_key": "min_media_types",
                "setting_value": "2",
                "value_type": "int",
                "description": "3-2-1-1-0ルール: 最小メディア種別数",
            },
            {
                "setting_key": "offline_update_warning_days",
                "setting_value": "7",
                "value_type": "int",
                "description": "オフラインメディア更新警告日数",
            },
            {
                "setting_key": "verification_reminder_days",
                "setting_value": "7",
                "value_type": "int",
                "description": "検証テストリマインダー日数",
            },
        ]

        for setting_data in settings:
            existing = SystemSetting.query.filter_by(setting_key=setting_data["setting_key"]).first()

            if not existing:
                setting = SystemSetting(**setting_data)
                db.session.add(setting)

        db.session.commit()
        click.echo("✓ システム設定初期化完了")

        click.echo("\n✅ データベース初期化が完了しました！")
        click.echo("\n次のステップ:")
        click.echo("  python scripts/create_admin.py - 管理者ユーザーを作成")


if __name__ == "__main__":
    init_database()

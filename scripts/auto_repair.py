#!/usr/bin/env python3
"""
自動修復エージェント - GitHub Issueから問題を検出し、自動的に修復を試みる
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class AutoRepairAgent:
    """自動修復エージェント"""

    def __init__(self, issue_number=None, max_retries=10, retry_interval=600):
        """
        Args:
            issue_number: 修復対象のIssue番号
            max_retries: 最大リトライ回数（デフォルト: 10回）
            retry_interval: リトライ間隔（秒）（デフォルト: 600秒 = 10分）
        """
        self.issue_number = issue_number
        self.max_retries = max_retries
        self.retry_interval = retry_interval
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.repo = os.environ.get("GITHUB_REPOSITORY", "Kensan196948G/backup-management-system")
        self.repair_log = []
        self.current_retry = 0

    def get_issue_details(self):
        """GitHub IssueからエラーCDを取得"""
        if not self.issue_number:
            print("❌ Issue number not provided")
            return None

        try:
            cmd = ["gh", "issue", "view", str(self.issue_number), "--json", "title,body,labels"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            issue_data = json.loads(result.stdout)

            # auto-repairラベルがあるか確認
            labels = [label["name"] for label in issue_data.get("labels", [])]
            if "auto-repair" not in labels:
                print("⚠️  This issue does not have 'auto-repair' label. Skipping.")
                return None

            # manual-repairラベルがあれば自動修復をスキップ
            if "manual-repair" in labels:
                print("⚠️  This issue has 'manual-repair' label. Skipping auto-repair.")
                return None

            return issue_data

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to get issue details: {e}")
            return None

    def analyze_errors(self, issue_body):
        """Issue本文からエラー内容を解析"""
        errors = []

        # エラーセクションを抽出
        if "### ❌ 検出されたエラー" in issue_body:
            error_section = issue_body.split("### ❌ 検出されたエラー")[1]
            error_section = error_section.split("###")[0]

            # エラー行を抽出
            for line in error_section.split("\n"):
                line = line.strip()
                if line and (line.startswith("1.") or line.startswith("❌")):
                    errors.append(line)

        return errors

    def repair_database_connection(self):
        """データベース接続エラーの修復"""
        print("🔧 Repairing database connection...")

        try:
            # データベースファイルの存在確認
            db_path = project_root / "instance" / "backup_system.db"
            if not db_path.exists():
                print("  📁 Database file not found. Creating new database...")

                # データベース初期化スクリプトを実行
                init_script = project_root / "scripts" / "init_db.py"
                if init_script.exists():
                    result = subprocess.run([sys.executable, str(init_script)], capture_output=True, text=True, check=True)
                    print("  ✅ Database initialized successfully")
                    self.repair_log.append("Database initialized")
                    return True
                else:
                    # 直接初期化
                    from app import create_app, db

                    app = create_app()
                    with app.app_context():
                        db.create_all()
                    print("  ✅ Database created successfully")
                    self.repair_log.append("Database created")
                    return True

            # データベース接続テスト
            from app import create_app, db

            app = create_app()
            with app.app_context():
                db.session.execute(db.text("SELECT 1"))
                print("  ✅ Database connection restored")
                self.repair_log.append("Database connection verified")
                return True

        except Exception as e:
            print(f"  ❌ Database repair failed: {e}")
            self.repair_log.append(f"Database repair failed: {str(e)}")
            return False

    def repair_flask_app(self):
        """Flask起動エラーの修復"""
        print("🔧 Repairing Flask application...")

        try:
            # 環境変数の確認
            if not os.environ.get("SECRET_KEY"):
                print("  📝 Generating SECRET_KEY...")
                import secrets

                secret_key = secrets.token_hex(32)
                env_file = project_root / ".env"

                # .envファイルに追加または更新
                env_content = ""
                if env_file.exists():
                    with open(env_file, "r") as f:
                        env_content = f.read()

                if "SECRET_KEY=" not in env_content:
                    with open(env_file, "a") as f:
                        f.write(f"\nSECRET_KEY={secret_key}\n")
                    print("  ✅ SECRET_KEY generated and saved")
                    self.repair_log.append("SECRET_KEY generated")

            # Flask起動テスト
            from app import create_app

            app = create_app()
            if app:
                print("  ✅ Flask app starts successfully")
                self.repair_log.append("Flask app verified")
                return True

        except Exception as e:
            print(f"  ❌ Flask repair failed: {e}")
            self.repair_log.append(f"Flask repair failed: {str(e)}")
            return False

    def repair_models_integrity(self):
        """モデル整合性エラーの修復"""
        print("🔧 Repairing models integrity...")

        try:
            # モデルのインポートテスト
            # データベーススキーマの更新
            from app import create_app, db
            from app.models import (
                Alert,
                BackupExecution,
                BackupJob,
                OfflineMedia,
                Report,
                User,
                VerificationTest,
            )

            app = create_app()
            with app.app_context():
                db.create_all()

            print("  ✅ Models integrity verified and schema updated")
            self.repair_log.append("Models integrity verified")
            return True

        except Exception as e:
            print(f"  ❌ Models repair failed: {e}")
            self.repair_log.append(f"Models repair failed: {str(e)}")
            return False

    def repair_routes(self):
        """ルートエラーの修復"""
        print("🔧 Repairing routes...")

        try:
            from app import create_app

            app = create_app()
            routes = [rule.rule for rule in app.url_map.iter_rules()]

            print(f"  ℹ️  Found {len(routes)} routes")
            print("  ✅ Routes verified")
            self.repair_log.append(f"Routes verified: {len(routes)} routes")
            return True

        except Exception as e:
            print(f"  ❌ Routes repair failed: {e}")
            self.repair_log.append(f"Routes repair failed: {str(e)}")
            return False

    def repair_templates(self):
        """テンプレートエラーの修復"""
        print("🔧 Checking templates...")

        template_dir = project_root / "app" / "templates"
        required_templates = [
            "base.html",
            "auth/login.html",
            "dashboard.html",
            "media/list.html",
            "verification/list.html",
            "reports/list.html",
        ]

        missing = []
        for template in required_templates:
            if not (template_dir / template).exists():
                missing.append(template)

        if missing:
            print(f"  ❌ Missing templates: {', '.join(missing)}")
            self.repair_log.append(f"Missing templates: {', '.join(missing)}")
            return False

        print("  ✅ All templates found")
        self.repair_log.append("Templates verified")
        return True

    def execute_repair(self, errors):
        """エラー内容に基づいて修復を実行"""
        print("\n" + "=" * 80)
        print(f"🔧 Starting Auto-Repair (Attempt {self.current_retry + 1}/{self.max_retries})")
        print("=" * 80)
        print()

        repair_results = []

        for error in errors:
            error_lower = error.lower()

            if "database" in error_lower:
                success = self.repair_database_connection()
                repair_results.append(("Database Connection", success))

            elif "flask" in error_lower or "startup" in error_lower:
                success = self.repair_flask_app()
                repair_results.append(("Flask App", success))

            elif "model" in error_lower:
                success = self.repair_models_integrity()
                repair_results.append(("Models", success))

            elif "route" in error_lower:
                success = self.repair_routes()
                repair_results.append(("Routes", success))

            elif "template" in error_lower:
                success = self.repair_templates()
                repair_results.append(("Templates", success))

        return repair_results

    def verify_repair(self):
        """修復後の検証"""
        print("\n" + "=" * 80)
        print("🔍 Verifying Repair...")
        print("=" * 80)
        print()

        # ヘルスチェックスクリプトを実行
        health_check_script = project_root / "scripts" / "health_check.py"

        try:
            result = subprocess.run([sys.executable, str(health_check_script)], capture_output=True, text=True, timeout=60)

            # 終了コード0なら成功
            if result.returncode == 0:
                print("✅ Verification passed! All systems healthy.")
                return True
            else:
                print("❌ Verification failed. Errors still exist.")
                print("\nHealth check output:")
                print(result.stdout)
                return False

        except subprocess.TimeoutExpired:
            print("❌ Verification timeout")
            return False
        except Exception as e:
            print(f"❌ Verification error: {e}")
            return False

    def update_issue(self, success, repair_results):
        """Issueに修復結果をコメント"""
        if not self.issue_number:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        if success:
            comment = f"""## ✅ 自動修復成功

**修復完了時刻**: {timestamp}
**試行回数**: {self.current_retry + 1}/{self.max_retries}

### 修復内容

"""
            for repair_name, result in repair_results:
                status = "✅ 成功" if result else "❌ 失敗"
                comment += f"- {repair_name}: {status}\n"

            comment += "\n### 検証結果\n\n✅ すべてのヘルスチェックが正常に完了しました。\n\n"
            comment += "このIssueは自動的にクローズされます。\n"

            # コメント追加
            try:
                subprocess.run(
                    ["gh", "issue", "comment", str(self.issue_number), "--body", comment],
                    check=True,
                    capture_output=True,
                )

                # Issueをクローズ
                subprocess.run(
                    ["gh", "issue", "close", str(self.issue_number), "--reason", "completed"],
                    check=True,
                    capture_output=True,
                )
                print(f"✅ Issue #{self.issue_number} closed successfully")

            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to update issue: {e}")

        else:
            comment = f"""## ⚠️  自動修復試行 ({self.current_retry + 1}/{self.max_retries})

**試行時刻**: {timestamp}

### 修復結果

"""
            for repair_name, result in repair_results:
                status = "✅ 成功" if result else "❌ 失敗"
                comment += f"- {repair_name}: {status}\n"

            if self.current_retry + 1 < self.max_retries:
                comment += f"\n### 次回試行\n\n{self.retry_interval // 60}分後に再度自動修復を試みます。\n"
            else:
                comment += "\n### 最大試行回数に達しました\n\n手動での対応が必要です。`manual-repair` ラベルを追加してください。\n"

            # コメント追加
            try:
                subprocess.run(
                    ["gh", "issue", "comment", str(self.issue_number), "--body", comment],
                    check=True,
                    capture_output=True,
                )
                print(f"✅ Issue #{self.issue_number} updated with repair attempt")

            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to update issue: {e}")

    def run_repair_loop(self):
        """修復ループを実行（最大10回、10分間隔）"""
        print("=" * 80)
        print("🤖 Auto-Repair Agent - Starting")
        print("=" * 80)
        print(f"Issue Number: #{self.issue_number}")
        print(f"Max Retries: {self.max_retries}")
        print(f"Retry Interval: {self.retry_interval}s ({self.retry_interval // 60}min)")
        print("=" * 80)
        print()

        # Issue詳細を取得
        issue_data = self.get_issue_details()
        if not issue_data:
            print("❌ Cannot retrieve issue data or issue not eligible for auto-repair")
            return False

        # エラー解析
        errors = self.analyze_errors(issue_data["body"])
        if not errors:
            print("⚠️  No errors found in issue body")
            return False

        print(f"📋 Detected {len(errors)} error(s) to repair:")
        for error in errors:
            print(f"  - {error}")
        print()

        # 修復ループ
        for retry in range(self.max_retries):
            self.current_retry = retry

            # 修復実行
            repair_results = self.execute_repair(errors)

            # 検証
            verification_success = self.verify_repair()

            # Issue更新
            self.update_issue(verification_success, repair_results)

            if verification_success:
                print("\n" + "=" * 80)
                print("✅ Auto-Repair Successful!")
                print("=" * 80)
                return True

            # 最大回数に達していない場合は待機
            if retry + 1 < self.max_retries:
                print(f"\n⏳ Waiting {self.retry_interval}s before next attempt...")
                print(f"Next attempt: {retry + 2}/{self.max_retries}")
                time.sleep(self.retry_interval)
            else:
                print("\n" + "=" * 80)
                print("❌ Maximum retries reached. Manual intervention required.")
                print("=" * 80)

        return False


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="Auto-repair agent for GitHub Issues")
    parser.add_argument("--issue", type=int, help="GitHub Issue number", required=True)
    parser.add_argument("--max-retries", type=int, default=10, help="Maximum retry attempts (default: 10)")
    parser.add_argument("--retry-interval", type=int, default=600, help="Retry interval in seconds (default: 600 = 10min)")

    args = parser.parse_args()

    agent = AutoRepairAgent(issue_number=args.issue, max_retries=args.max_retries, retry_interval=args.retry_interval)

    success = agent.run_repair_loop()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

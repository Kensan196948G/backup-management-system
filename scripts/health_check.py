#!/usr/bin/env python3
"""
ヘルスチェックスクリプト - システムの健全性を監視し、エラーを検知
エラー検出時にGitHub Issueを自動作成します
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class HealthChecker:
    """システムヘルスチェッカー"""

    def __init__(self):
        self.errors = []
        self.warnings = []
        self.checks_passed = []
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.repo = os.environ.get("GITHUB_REPOSITORY", "Kensan196948G/backup-management-system")

    def check_database_connection(self):
        """データベース接続チェック"""
        try:
            from app import create_app, db

            app = create_app()
            with app.app_context():
                # 簡単なクエリでDB接続を確認
                db.session.execute(db.text("SELECT 1"))
                self.checks_passed.append("✅ Database connection: OK")
                return True
        except Exception as e:
            error_msg = f"❌ Database connection failed: {str(e)}"
            self.errors.append(error_msg)
            return False

    def check_flask_app_startup(self):
        """Flaskアプリケーション起動チェック"""
        try:
            from app import create_app

            app = create_app()
            if app:
                self.checks_passed.append("✅ Flask app startup: OK")
                return True
        except Exception as e:
            error_msg = f"❌ Flask app startup failed: {str(e)}"
            self.errors.append(error_msg)
            return False

    def check_models_integrity(self):
        """モデル整合性チェック"""
        try:
            from app.models import (
                Alert,
                BackupExecution,
                BackupJob,
                OfflineMedia,
                Report,
                User,
                VerificationTest,
            )

            # 各モデルが正しくインポートできるか確認
            models = [User, BackupJob, BackupExecution, OfflineMedia, VerificationTest, Report, Alert]
            for model in models:
                if not hasattr(model, "__tablename__"):
                    raise ValueError(f"Model {model.__name__} has no __tablename__")

            self.checks_passed.append("✅ Models integrity: OK")
            return True
        except Exception as e:
            error_msg = f"❌ Models integrity check failed: {str(e)}"
            self.errors.append(error_msg)
            return False

    def check_routes(self):
        """ルート定義チェック"""
        try:
            from app import create_app

            app = create_app()
            routes = [rule.rule for rule in app.url_map.iter_rules()]

            # 重要なルートが存在するか確認
            required_routes = ["/", "/auth/login", "/dashboard/", "/api/dashboard/stats"]

            missing_routes = [route for route in required_routes if route not in routes]

            if missing_routes:
                error_msg = f"❌ Missing required routes: {', '.join(missing_routes)}"
                self.errors.append(error_msg)
                return False

            self.checks_passed.append(f"✅ Routes check: OK ({len(routes)} routes)")
            return True
        except Exception as e:
            error_msg = f"❌ Routes check failed: {str(e)}"
            self.errors.append(error_msg)
            return False

    def check_templates(self):
        """テンプレートファイルチェック"""
        try:
            template_dir = project_root / "app" / "templates"
            required_templates = [
                "base.html",
                "auth/login.html",
                "dashboard.html",
                "media/list.html",
                "verification/list.html",
                "reports/list.html",
            ]

            missing_templates = []
            for template in required_templates:
                template_path = template_dir / template
                if not template_path.exists():
                    missing_templates.append(template)

            if missing_templates:
                error_msg = f"❌ Missing templates: {', '.join(missing_templates)}"
                self.errors.append(error_msg)
                return False

            self.checks_passed.append(f"✅ Templates check: OK")
            return True
        except Exception as e:
            error_msg = f"❌ Templates check failed: {str(e)}"
            self.errors.append(error_msg)
            return False

    def check_environment_variables(self):
        """環境変数チェック"""
        required_env_vars = ["SECRET_KEY", "FLASK_ENV"]
        missing_vars = [var for var in required_env_vars if not os.environ.get(var)]

        if missing_vars:
            warning_msg = f"⚠️  Missing environment variables: {', '.join(missing_vars)}"
            self.warnings.append(warning_msg)
            return False

        self.checks_passed.append("✅ Environment variables: OK")
        return True

    def run_all_checks(self):
        """すべてのヘルスチェックを実行"""
        print("=" * 80)
        print("🏥 System Health Check - Starting")
        print("=" * 80)
        print()

        checks = [
            ("Database Connection", self.check_database_connection),
            ("Flask App Startup", self.check_flask_app_startup),
            ("Models Integrity", self.check_models_integrity),
            ("Routes", self.check_routes),
            ("Templates", self.check_templates),
            ("Environment Variables", self.check_environment_variables),
        ]

        for check_name, check_func in checks:
            print(f"Running: {check_name}...")
            check_func()
            print()

        # 結果サマリー
        print("=" * 80)
        print("📊 Health Check Results")
        print("=" * 80)
        print()

        if self.checks_passed:
            print("✅ Passed Checks:")
            for check in self.checks_passed:
                print(f"  {check}")
            print()

        if self.warnings:
            print("⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  {warning}")
            print()

        if self.errors:
            print("❌ Errors:")
            for error in self.errors:
                print(f"  {error}")
            print()

        return len(self.errors) == 0

    def create_github_issue(self):
        """GitHub Issueを自動作成"""
        if not self.errors:
            print("No errors detected. Skipping issue creation.")
            return None

        if not self.github_token:
            print("⚠️  GITHUB_TOKEN not found. Cannot create issue.")
            return None

        # Issue本文を作成
        issue_title = f"🔴 Auto-detected System Errors - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        issue_body = f"""## 🚨 自動検知されたシステムエラー

**検知時刻**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

### ❌ 検出されたエラー

"""

        for i, error in enumerate(self.errors, 1):
            issue_body += f"{i}. {error}\n"

        issue_body += "\n### ✅ 正常なチェック\n\n"
        for check in self.checks_passed:
            issue_body += f"- {check}\n"

        if self.warnings:
            issue_body += "\n### ⚠️  警告\n\n"
            for warning in self.warnings:
                issue_body += f"- {warning}\n"

        issue_body += """

---

### 🤖 自動修復について

このIssueは自動ヘルスチェックシステムによって作成されました。
自動修復ワークフローが10分以内に起動し、問題の修復を試みます。

**自動修復プロセス**:
1. エラー内容の分析
2. 修復スクリプトの実行
3. 修復後の検証
4. 成功時: Issue自動クローズ
5. 失敗時: 10分後に再試行（最大10回）

**ラベル**: `auto-repair`, `bug`, `automated`

このIssueを手動で修復する場合は、`manual-repair` ラベルを追加してください。
"""

        # gh CLIを使用してIssueを作成
        try:
            issue_data = {
                "title": issue_title,
                "body": issue_body,
                "labels": ["auto-repair", "bug", "automated"],
            }

            # gh issue createコマンドを実行
            cmd = [
                "gh",
                "issue",
                "create",
                "--title",
                issue_title,
                "--body",
                issue_body,
                "--label",
                "auto-repair,bug,automated",
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            issue_url = result.stdout.strip()
            print(f"✅ GitHub Issue created: {issue_url}")

            # Issue番号を抽出
            issue_number = issue_url.split("/")[-1]

            return {
                "issue_number": issue_number,
                "issue_url": issue_url,
                "errors": self.errors,
                "warnings": self.warnings,
            }

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to create GitHub Issue: {e}")
            print(f"stderr: {e.stderr}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error creating issue: {e}")
            return None

    def save_error_report(self, issue_data=None):
        """エラーレポートをJSONファイルに保存"""
        report_dir = project_root / "logs" / "health_checks"
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"health_check_{timestamp}.json"

        report = {
            "timestamp": datetime.now().isoformat(),
            "errors": self.errors,
            "warnings": self.warnings,
            "checks_passed": self.checks_passed,
            "issue_data": issue_data,
        }

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📄 Error report saved: {report_file}")
        return report_file


def main():
    """メイン処理"""
    checker = HealthChecker()

    # ヘルスチェック実行
    all_checks_passed = checker.run_all_checks()

    # エラーがあればIssue作成
    issue_data = None
    if not all_checks_passed:
        print("\n" + "=" * 80)
        print("🚨 Errors detected. Creating GitHub Issue...")
        print("=" * 80)
        print()
        issue_data = checker.create_github_issue()

    # レポート保存
    report_file = checker.save_error_report(issue_data)

    # 終了コード
    if all_checks_passed:
        print("\n✅ All health checks passed!")
        sys.exit(0)
    else:
        print(f"\n❌ Health checks failed with {len(checker.errors)} error(s)")
        sys.exit(1)


if __name__ == "__main__":
    main()

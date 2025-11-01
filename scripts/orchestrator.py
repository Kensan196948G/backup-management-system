#!/usr/bin/env python3
"""
Git Worktree 並列開発オーケストレーター
8体のエージェントの状態監視、統合管理、依存関係チェック
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
WORKTREE_BASE = PROJECT_ROOT.parent / "worktrees"

# エージェント定義
AGENTS = {
    "01": {
        "name": "Core Backup Engine",
        "worktree": "agent-01-core",
        "branch": "feature/backup-engine",
        "priority": "CRITICAL",
        "dependencies": [],
    },
    "02": {
        "name": "Storage Management",
        "worktree": "agent-02-storage",
        "branch": "feature/storage-management",
        "priority": "CRITICAL",
        "dependencies": [],
    },
    "03": {
        "name": "Verification & Validation",
        "worktree": "agent-03-verification",
        "branch": "feature/verification-validation",
        "priority": "HIGH",
        "dependencies": ["01", "02"],
    },
    "04": {
        "name": "Scheduler & Job Manager",
        "worktree": "agent-04-scheduler",
        "branch": "feature/job-scheduler",
        "priority": "HIGH",
        "dependencies": ["01", "02"],
    },
    "05": {
        "name": "Alert & Notification",
        "worktree": "agent-05-alerts",
        "branch": "feature/alert-notification",
        "priority": "MEDIUM",
        "dependencies": ["01", "03"],
    },
    "06": {
        "name": "Web UI & Dashboard",
        "worktree": "agent-06-web",
        "branch": "feature/web-ui",
        "priority": "MEDIUM",
        "dependencies": ["01", "02", "04", "05"],
    },
    "07": {
        "name": "API & Integration Layer",
        "worktree": "agent-07-api",
        "branch": "feature/api-layer",
        "priority": "MEDIUM",
        "dependencies": ["01", "02", "03", "04", "05"],
    },
    "08": {
        "name": "Documentation & Compliance",
        "worktree": "agent-08-docs",
        "branch": "feature/documentation",
        "priority": "LOW",
        "dependencies": ["01", "02", "03", "04", "05", "06", "07"],
    },
}


class AgentOrchestrator:
    """エージェントオーケストレーター"""

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.worktree_base = WORKTREE_BASE

    def get_agent_status(self, agent_id: str) -> Dict:
        """エージェントの状態を取得"""
        agent = AGENTS[agent_id]
        worktree_path = self.worktree_base / agent["worktree"]

        if not worktree_path.exists():
            return {"agent_id": agent_id, "name": agent["name"], "status": "NOT_CREATED", "worktree_exists": False}

        # Git情報を取得
        try:
            # 未コミットファイル数
            result = subprocess.run(
                ["git", "status", "--porcelain"], cwd=worktree_path, capture_output=True, text=True, check=True
            )
            uncommitted_files = len([line for line in result.stdout.split("\n") if line.strip()])

            # 現在のブランチ
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=worktree_path, capture_output=True, text=True, check=True
            )
            current_branch = result.stdout.strip()

            # mainとの差分 (ahead/behind)
            result = subprocess.run(
                ["git", "rev-list", "--left-right", "--count", f"origin/main...{current_branch}"],
                cwd=worktree_path,
                capture_output=True,
                text=True,
                check=True,
            )
            behind, ahead = map(int, result.stdout.strip().split())

            # 最終コミット時刻
            result = subprocess.run(
                ["git", "log", "-1", "--format=%ci"], cwd=worktree_path, capture_output=True, text=True, check=True
            )
            last_commit_time = result.stdout.strip() if result.stdout.strip() else "N/A"

            # 状態判定
            if uncommitted_files == 0 and ahead == 0 and behind == 0:
                status = "UP_TO_DATE"
                status_emoji = "🟢"
            elif uncommitted_files > 0 and uncommitted_files <= 10:
                status = "HAS_CHANGES"
                status_emoji = "🟡"
            elif behind > 0 and behind <= 20:
                status = "BEHIND"
                status_emoji = "🟡"
            elif behind > 20:
                status = "NEEDS_SYNC"
                status_emoji = "🟠"
            elif uncommitted_files > 10:
                status = "TOO_MANY_CHANGES"
                status_emoji = "🔴"
            else:
                status = "ACTIVE"
                status_emoji = "🟢"

            return {
                "agent_id": agent_id,
                "name": agent["name"],
                "worktree_path": str(worktree_path),
                "branch": current_branch,
                "status": status,
                "status_emoji": status_emoji,
                "uncommitted_files": uncommitted_files,
                "ahead_main": ahead,
                "behind_main": behind,
                "last_commit_time": last_commit_time,
                "worktree_exists": True,
                "priority": agent["priority"],
                "dependencies": agent["dependencies"],
            }

        except subprocess.CalledProcessError as e:
            return {
                "agent_id": agent_id,
                "name": agent["name"],
                "status": "ERROR",
                "status_emoji": "🔴",
                "error": str(e),
                "worktree_exists": True,
            }

    def show_status(self, agent_ids: Optional[List[str]] = None):
        """全エージェントまたは指定エージェントの状態を表示"""
        if agent_ids is None:
            agent_ids = sorted(AGENTS.keys())

        print("=" * 100)
        print("  Git Worktree 並列開発 - エージェント状態")
        print(f"  更新時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        print()

        for agent_id in agent_ids:
            status = self.get_agent_status(agent_id)

            print(f"{status.get('status_emoji', '❓')} Agent-{agent_id}: {status['name']}")
            print(f"   ステータス: {status['status']}")

            if status.get("worktree_exists"):
                print(f"   ブランチ: {status.get('branch', 'N/A')}")
                print(f"   未コミット: {status.get('uncommitted_files', 0)} ファイル")
                ahead = status.get("ahead_main", 0)
                behind = status.get("behind_main", 0)
                print(f"   Ahead/Behind: +{ahead}/-{behind}")
                behind = status.get("behind_main", 0)
                print(f"   Ahead/Behind: +{ahead}/-{behind}")
                print(f"   最終コミット: {status.get('last_commit_time', 'N/A')}")
                print(f"   優先度: {status.get('priority', 'N/A')}")
                print(f"   依存: {', '.join(['Agent-' + d for d in status.get('dependencies', [])]) or 'なし'}")
            else:
                print("   ⚠️  Worktreeが作成されていません")

            print()

    def check_dependencies(self, agent_id: str) -> bool:
        """エージェントの依存関係をチェック"""
        agent = AGENTS[agent_id]
        dependencies = agent["dependencies"]

        if not dependencies:
            return True

        print(f"Agent-{agent_id} の依存関係をチェック中...")
        print()

        all_ok = True
        for dep_id in dependencies:
            dep_status = self.get_agent_status(dep_id)

            if dep_status["status"] == "UP_TO_DATE":
                print(f"  ✅ Agent-{dep_id} ({dep_status['name']}): 統合準備完了")
            elif dep_status["status"] in ["HAS_CHANGES", "AHEAD"]:
                print(f"  ⚠️  Agent-{dep_id} ({dep_status['name']}): 未コミットまたは未統合")
                all_ok = False
            else:
                print(f"  ❌ Agent-{dep_id} ({dep_status['name']}): {dep_status['status']}")
                all_ok = False

        print()
        if all_ok:
            print(f"✅ Agent-{agent_id} の統合準備が整っています")
        else:
            print(f"❌ Agent-{agent_id} の依存エージェントが未準備です")

        return all_ok

    def integrate_agent(self, agent_id: str, dry_run: bool = False):
        """エージェントをmainブランチに統合"""
        agent = AGENTS[agent_id]
        worktree_path = self.worktree_base / agent["worktree"]
        branch = agent["branch"]

        print("=" * 80)
        print(f"  Agent-{agent_id} ({agent['name']}) 統合プロセス")
        print("=" * 80)
        print()

        # 依存関係チェック
        if not self.check_dependencies(agent_id):
            print("❌ 依存関係が満たされていないため、統合を中止します")
            return False

        # ステータス確認
        status = self.get_agent_status(agent_id)

        if status["uncommitted_files"] > 0:
            print(f"❌ 未コミットファイルが {status['uncommitted_files']} 件あります")
            print("   先にコミットしてください")
            return False

        if status["ahead_main"] == 0:
            print("⚠️  mainブランチとの差分がありません（統合不要）")
            return True

        print(f"📋 統合内容:")
        print(f"   ブランチ: {branch}")
        print(f"   コミット数: {status['ahead_main']}")
        print()

        if dry_run:
            print("🔍 DRY RUN モード - 実際の統合は行いません")
            print(f"   以下のコマンドが実行される予定:")
            print(f"   git checkout main")
            print(f"   git pull origin main")
            print(f"   git merge --no-ff {branch}")
            print(f"   git push origin main")
            return True

        # 実際の統合処理
        try:
            # mainブランチに切り替え
            print("1. mainブランチに切り替え中...")
            subprocess.run(["git", "checkout", "main"], cwd=self.project_root, check=True)

            # mainブランチを最新化
            print("2. mainブランチを最新化中...")
            subprocess.run(["git", "pull", "origin", "main"], cwd=self.project_root, check=True)

            # エージェントブランチをマージ
            print(f"3. {branch} をマージ中...")
            subprocess.run(
                ["git", "merge", "--no-ff", "-m", f"Merge {branch}: {agent['name']}"], cwd=self.project_root, check=True
            )

            # mainブランチにプッシュ
            print("4. mainブランチにプッシュ中...")
            subprocess.run(["git", "push", "origin", "main"], cwd=self.project_root, check=True)

            print()
            print(f"✅ Agent-{agent_id} の統合が完了しました")
            return True

        except subprocess.CalledProcessError as e:
            print()
            print(f"❌ 統合中にエラーが発生しました: {e}")
            print("   コンフリクトが発生した可能性があります")
            print("   conflicts/ ディレクトリに記録して手動で解決してください")
            return False

    def sync_all_agents(self):
        """全エージェントをmainブランチと同期"""
        print("=" * 80)
        print("  全エージェントをmainブランチと同期")
        print("=" * 80)
        print()

        for agent_id in sorted(AGENTS.keys()):
            agent = AGENTS[agent_id]
            worktree_path = self.worktree_base / agent["worktree"]

            if not worktree_path.exists():
                print(f"⚠️  Agent-{agent_id}: Worktreeが存在しません（スキップ）")
                continue

            print(f"🔄 Agent-{agent_id} ({agent['name']}) を同期中...")

            try:
                # mainから最新を取得
                subprocess.run(["git", "fetch", "origin", "main"], cwd=worktree_path, check=True, capture_output=True)

                # マージ
                subprocess.run(["git", "merge", "origin/main"], cwd=worktree_path, check=True, capture_output=True)

                print(f"   ✅ 同期完了")

            except subprocess.CalledProcessError as e:
                print(f"   ❌ 同期失敗: {e}")

            print()


def main():
    parser = argparse.ArgumentParser(description="Git Worktree並列開発オーケストレーター")

    subparsers = parser.add_subparsers(dest="command", help="コマンド")

    # statusコマンド
    status_parser = subparsers.add_parser("status", help="エージェントの状態表示")
    status_parser.add_argument("agent_id", nargs="?", help="エージェントID (01-08)")

    # depsコマンド
    deps_parser = subparsers.add_parser("deps", help="依存関係チェック")
    deps_parser.add_argument("agent_id", help="エージェントID (01-08)")

    # integrateコマンド
    integrate_parser = subparsers.add_parser("integrate", help="エージェントを統合")
    integrate_parser.add_argument("agent_id", help="エージェントID (01-08)")
    integrate_parser.add_argument("--dry-run", action="store_true", help="実行内容を表示のみ")

    # syncコマンド
    sync_parser = subparsers.add_parser("sync", help="全エージェントをmainと同期")

    args = parser.parse_args()

    orchestrator = AgentOrchestrator()

    if args.command == "status":
        if args.agent_id:
            orchestrator.show_status([args.agent_id])
        else:
            orchestrator.show_status()

    elif args.command == "deps":
        orchestrator.check_dependencies(args.agent_id)

    elif args.command == "integrate":
        orchestrator.integrate_agent(args.agent_id, dry_run=args.dry_run)

    elif args.command == "sync":
        orchestrator.sync_all_agents()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

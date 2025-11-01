#!/bin/bash
################################################################################
# Git Worktree 並列開発環境セットアップスクリプト
# 3-2-1-1-0 バックアップ管理システム - 8エージェント構成
################################################################################

set -e  # エラー時に停止

# カラー出力設定
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ロギング関数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# プロジェクトルートの確認
if [ ! -d ".git" ]; then
    log_error "このスクリプトはGitリポジトリのルートディレクトリで実行してください"
    exit 1
fi

PROJECT_ROOT=$(pwd)
WORKTREE_BASE="${PROJECT_ROOT}/../worktrees"

log_info "======================================================================"
log_info "  Git Worktree 並列開発環境セットアップ"
log_info "  プロジェクト: 3-2-1-1-0 バックアップ管理システム"
log_info "  エージェント数: 8"
log_info "======================================================================"
echo

# Worktreeベースディレクトリ作成
log_info "Worktreeベースディレクトリを作成: ${WORKTREE_BASE}"
mkdir -p "${WORKTREE_BASE}"

# エージェント定義
declare -A AGENTS
AGENTS[01]="agent-01-core:feature/backup-engine:Core Backup Engine"
AGENTS[02]="agent-02-storage:feature/storage-management:Storage Management"
AGENTS[03]="agent-03-verification:feature/verification-validation:Verification & Validation"
AGENTS[04]="agent-04-scheduler:feature/job-scheduler:Scheduler & Job Manager"
AGENTS[05]="agent-05-alerts:feature/alert-notification:Alert & Notification"
AGENTS[06]="agent-06-web:feature/web-ui:Web UI & Dashboard"
AGENTS[07]="agent-07-api:feature/api-layer:API & Integration Layer"
AGENTS[08]="agent-08-docs:feature/documentation:Documentation & Compliance"

# 各エージェント用のworktreeとブランチを作成
for agent_id in $(echo "${!AGENTS[@]}" | tr ' ' '\n' | sort); do
    IFS=':' read -r worktree_name branch_name description <<< "${AGENTS[$agent_id]}"

    WORKTREE_PATH="${WORKTREE_BASE}/${worktree_name}"

    echo
    log_info "────────────────────────────────────────────────────────────────"
    log_info "Agent-${agent_id}: ${description}"
    log_info "  ブランチ: ${branch_name}"
    log_info "  Worktree: ${WORKTREE_PATH}"
    log_info "────────────────────────────────────────────────────────────────"

    # ブランチが既に存在するか確認
    if git show-ref --verify --quiet "refs/heads/${branch_name}"; then
        log_warning "ブランチ ${branch_name} は既に存在します（スキップ）"
    else
        log_info "ブランチを作成: ${branch_name}"
        git branch "${branch_name}" develop 2>/dev/null || git branch "${branch_name}" main
        log_success "ブランチ作成完了"
    fi

    # Worktreeが既に存在するか確認
    if [ -d "${WORKTREE_PATH}" ]; then
        log_warning "Worktree ${WORKTREE_PATH} は既に存在します（スキップ）"
    else
        log_info "Worktreeを作成: ${WORKTREE_PATH}"
        git worktree add "${WORKTREE_PATH}" "${branch_name}"
        log_success "Worktree作成完了"

        # 設定ファイルをコピー
        log_info "設定ファイルをコピー中..."

        if [ -f "${PROJECT_ROOT}/.editorconfig" ]; then
            cp "${PROJECT_ROOT}/.editorconfig" "${WORKTREE_PATH}/"
            log_success ".editorconfig コピー完了"
        fi

        if [ -f "${PROJECT_ROOT}/.flake8" ]; then
            cp "${PROJECT_ROOT}/.flake8" "${WORKTREE_PATH}/"
            log_success ".flake8 コピー完了"
        fi

        if [ -f "${PROJECT_ROOT}/pyproject.toml" ]; then
            cp "${PROJECT_ROOT}/pyproject.toml" "${WORKTREE_PATH}/"
            log_success "pyproject.toml コピー完了"
        fi

        if [ -f "${PROJECT_ROOT}/.gitignore" ]; then
            cp "${PROJECT_ROOT}/.gitignore" "${WORKTREE_PATH}/"
            log_success ".gitignore コピー完了"
        fi

        # エージェント専用ディレクトリ作成
        mkdir -p "${WORKTREE_PATH}/logs/agent-${agent_id}"
        log_success "ログディレクトリ作成: logs/agent-${agent_id}"

        # AGENT_README.md作成（プレースホルダー）
        cat > "${WORKTREE_PATH}/AGENT_README.md" << EOF
# Agent-${agent_id}: ${description}

## 役割

このエージェントは「${description}」を担当します。

## ブランチ

\`${branch_name}\`

## 担当ファイル

（TODO: このエージェントが担当するファイル・ディレクトリを記載）

## 依存関係

（TODO: 依存する他のエージェントを記載）

## 開発手順

1. 朝: mainブランチから最新を取得
   \`\`\`bash
   git fetch origin main
   git merge origin main
   \`\`\`

2. 開発中: 小さな単位でコミット
   \`\`\`bash
   git add <files>
   git commit -m "[AGENT-${agent_id}] type: description"
   \`\`\`

3. 夕方: テスト実行とプッシュ
   \`\`\`bash
   pytest tests/
   git push origin ${branch_name}
   \`\`\`

## 進捗ログ

\`logs/agent-${agent_id}/progress.md\` に日々の進捗を記録してください。

## 参考資料

- [Git Worktree並列開発ガイド](../../docs/GIT_WORKTREE_PARALLEL_DEV.md)
- [ISO 27001準拠要件](../../docs/ISO_27001_COMPLIANCE.md)
- [ISO 19650準拠要件](../../docs/ISO_19650_COMPLIANCE.md)
EOF
        log_success "AGENT_README.md 作成完了"

        # 進捗ログテンプレート作成
        cat > "${WORKTREE_PATH}/logs/agent-${agent_id}/progress.md" << EOF
# Agent-${agent_id} Progress Log

## $(date +%Y-%m-%d)

### Morning
-

### Afternoon
-

### Evening
-

### Metrics
- Lines of code added:
- Lines of code removed:
- Test coverage:
- Commits:

### Tomorrow's Plan
- [ ]
EOF
        log_success "progress.md テンプレート作成完了"
    fi
done

# 統合管理用ディレクトリ作成
echo
log_info "======================================================================"
log_info "統合管理用ディレクトリを作成"
log_info "======================================================================"

mkdir -p "${PROJECT_ROOT}/conflicts"
mkdir -p "${PROJECT_ROOT}/integration-questions"

for agent_id in 01 02 03 04 05 06 07 08; do
    mkdir -p "${PROJECT_ROOT}/integration-questions/agent-${agent_id}"
done

log_success "統合管理ディレクトリ作成完了"

# STATUS.md作成
if [ ! -f "${PROJECT_ROOT}/STATUS.md" ]; then
    log_info "STATUS.md を作成中..."
    cat > "${PROJECT_ROOT}/STATUS.md" << 'EOF'
# 3-2-1-1-0 Backup System - Development Status

Last Updated: $(date +%Y-%m-%d\ %H:%M)

## Overall Progress

- [ ] Agent-01: Core Backup Engine (0%)
- [ ] Agent-02: Storage Management (0%)
- [ ] Agent-03: Verification & Validation (0%)
- [ ] Agent-04: Scheduler & Job Manager (0%)
- [ ] Agent-05: Alert & Notification (0%)
- [ ] Agent-06: Web UI & Dashboard (0%)
- [ ] Agent-07: API & Integration Layer (0%)
- [ ] Agent-08: Documentation & Compliance (0%)

## Current Sprint

Sprint: 1
Duration: TBD

### Sprint Goals

1. Establish core infrastructure (Agent-01, Agent-02)
2. Define interfaces between agents
3. Set up development environment and worktrees

## Agent Status

### Agent-01: Core Backup Engine
- Status: 🔴 NOT_STARTED
- Last Activity: N/A
- Completed: []
- In Progress: []
- Blockers: []

### Agent-02: Storage Management
- Status: 🔴 NOT_STARTED
- Last Activity: N/A
- Completed: []
- In Progress: []
- Blockers: []

### Agent-03: Verification & Validation
- Status: 🔴 NOT_STARTED
- Last Activity: N/A
- Completed: []
- In Progress: []
- Blockers: []

### Agent-04: Scheduler & Job Manager
- Status: 🔴 NOT_STARTED
- Last Activity: N/A
- Completed: []
- In Progress: []
- Blockers: []

### Agent-05: Alert & Notification
- Status: 🔴 NOT_STARTED
- Last Activity: N/A
- Completed: []
- In Progress: []
- Blockers: []

### Agent-06: Web UI & Dashboard
- Status: 🔴 NOT_STARTED
- Last Activity: N/A
- Completed: []
- In Progress: []
- Blockers: []

### Agent-07: API & Integration Layer
- Status: 🔴 NOT_STARTED
- Last Activity: N/A
- Completed: []
- In Progress: []
- Blockers: []

### Agent-08: Documentation & Compliance
- Status: 🔴 NOT_STARTED
- Last Activity: N/A
- Completed: []
- In Progress: []
- Blockers: []

## Integration Points

### Ready for Integration
- None yet

### Pending Integration
- TBD

## Blockers & Issues

### Critical
- None

### High
- None

### Medium
- None

## Next Week's Focus

1. Setup complete development environment
2. Begin Agent-01 and Agent-02 implementation
3. Define interfaces between agents
EOF
    log_success "STATUS.md 作成完了"
fi

# CURRENT_CONFLICTS.txt作成
if [ ! -f "${PROJECT_ROOT}/conflicts/CURRENT_CONFLICTS.txt" ]; then
    log_info "CURRENT_CONFLICTS.txt を作成中..."
    cat > "${PROJECT_ROOT}/conflicts/CURRENT_CONFLICTS.txt" << EOF
# Current Conflicts

Last Updated: $(date +%Y-%m-%d\ %H:%M)

## Active Conflicts

None

## Resolved Conflicts

(履歴がここに追加されます)
EOF
    log_success "CURRENT_CONFLICTS.txt 作成完了"
fi

# 完了メッセージ
echo
log_info "======================================================================"
log_success "🎉 Git Worktree 並列開発環境のセットアップが完了しました！"
log_info "======================================================================"
echo
log_info "作成されたWorktree一覧:"
echo

git worktree list

echo
log_info "次のステップ:"
log_info "1. 各worktreeに移動してClaude Codeを起動"
log_info "   cd ${WORKTREE_BASE}/agent-01-core"
log_info "   # Claude Codeを起動し、AGENT_README.mdの内容をプロンプトとして提供"
echo
log_info "2. オーケストレータースクリプトで状態確認"
log_info "   python scripts/orchestrator.py status"
echo
log_info "3. 詳細なガイドは以下を参照:"
log_info "   docs/GIT_WORKTREE_PARALLEL_DEV.md"
echo
log_success "Happy coding! 🚀"

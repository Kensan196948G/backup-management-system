# Agent機能・Hooks並列開発システム セットアップガイド
# 3-2-1-1-0 バックアップ管理システム

**作成日**: 2025年10月30日
**バージョン**: 1.0
**ステータス**: ✅ 設定完了

---

## 🎉 セットアップ完了状況

### ✅ 完了した設定

1. **Agent通信インフラ** ✅
   - [project-state.json](agent-communication/project-state.json) - プロジェクト状態管理
   - [dependency_resolver.py](agent-communication/dependency_resolver.py) - 依存関係解決

2. **Git Hooks** ✅
   - `.git/hooks/pre-commit` - コミット前チェック
   - `.git/hooks/pre-push` - プッシュ前テスト
   - `.git/hooks/post-merge` - マージ後処理

3. **GitHub Actions CI/CD** ✅
   - `.github/workflows/ci.yml` - 継続的インテグレーション

4. **ディレクトリ構造** ✅
   - すべての必要なディレクトリを作成済み

---

## 📊 Agent システム概要

### 10体のサブエージェント

1. **Agent 1: PM (プロジェクトマネージャー)**
   - タスク分解・優先順位付け
   - 進捗管理・調整

2. **Agent 2: Database (データベースアーキテクト)**
   - SQLAlchemyモデル実装
   - マイグレーション管理

3. **Agent 3: Backend API (バックエンドAPI開発)**
   - REST APIエンドポイント実装
   - ビジネスロジック統合

4. **Agent 4: Frontend (フロントエンド開発)**
   - Webページ・テンプレート実装
   - レスポンシブデザイン

5. **Agent 5: Security (認証・セキュリティ)**
   - Flask-Login統合
   - RBAC実装

6. **Agent 6: Logic (ビジネスロジック)**
   - 3-2-1-1-0チェックロジック
   - コンプライアンス計算

7. **Agent 7: Scheduler (スケジューラー・通知)**
   - APScheduler設定
   - メール・Teams通知

8. **Agent 8: PowerShell (PowerShell統合)**
   - Windows環境統合
   - デプロイスクリプト

9. **Agent 9: Test (テストエンジニア)**
   - Pytestによるテスト作成
   - カバレッジ管理

10. **Agent 10: DevOps (デプロイ)**
    - CI/CD設定
    - 環境構築自動化

---

## 🚀 使用方法

### 1. Agent状態の確認

```bash
# プロジェクト状態を確認
cat docs/agent-communication/project-state.json
```

### 2. 依存関係の管理

```python
# 依存関係解決ツールの使用
cd docs/agent-communication
python3 dependency_resolver.py
```

### 3. Git Hooksの動作確認

```bash
# pre-commitフックのテスト
git add .
git commit -m "Test commit"

# pre-pushフックのテスト
git push origin develop
```

### 4. CI/CDパイプラインの確認

GitHubにプッシュすると自動的に：
- リントチェック実行
- テスト実行
- セキュリティスキャン
- ビルド作成

---

## 📝 Agent開発ワークフロー

### ステップ1: タスク取得

```bash
# Agent 1 (PM) がタスクを作成
# GitHub Issues で確認
```

### ステップ2: ブランチ作成

```bash
# 例: Agent 2 (Database) の場合
git checkout develop
git checkout -b feature/database-models
```

### ステップ3: 開発

```bash
# コードを実装
# Git Hooksが自動的にチェック
```

### ステップ4: コミット・プッシュ

```bash
git add .
git commit -m "feat: implement database models"
git push origin feature/database-models
```

### ステップ5: Pull Request作成

```bash
# GitHub で PR作成
# CI/CDが自動実行
# レビュー後マージ
```

---

## 🔧 Git Hooks詳細

### pre-commit (コミット前)

自動実行内容:
- ✅ Python構文チェック
- ✅ flake8リントチェック
- ✅ black自動フォーマット
- ✅ isort インポート整理

### pre-push (プッシュ前)

自動実行内容:
- ✅ pytest単体テスト実行

### post-merge (マージ後)

自動実行内容:
- ✅ requirements.txt更新時: pip install
- ✅ マイグレーション更新時: flask db upgrade
- ✅ package.json更新時: npm install

---

## 📋 GitHub Actions CI/CD

### トリガー

- `push` to `develop` or `main`
- `pull_request` to `develop` or `main`

### ジョブ

1. **lint** - コード品質チェック
   - flake8
   - black
   - isort

2. **test** - テスト実行
   - pytest
   - カバレッジ測定

3. **security** - セキュリティスキャン
   - bandit

4. **build** - ビルド作成
   - デプロイメントパッケージ作成

---

## 🎯 並列開発の実現

### 依存関係グラフ

```
Agent-1 (PM) → タスク割り当て
    ↓
    ├→ Agent-2 (Database)
    │      ↓
    │      ├→ Agent-3 (API)
    │      ├→ Agent-6 (Logic)
    │      └→ Agent-9 (Test)
    │
    ├→ Agent-4 (Frontend) - 並列
    ├→ Agent-8 (PowerShell) - 独立
    └→ Agent-10 (DevOps) - 最初に実行
```

### 並列開発例

```bash
# 同時に3つのAgentが作業可能

# Agent 2: Database
git checkout -b feature/database-models
# ... 開発 ...

# Agent 4: Frontend (並列)
git checkout -b feature/dashboard-ui
# ... 開発 ...

# Agent 10: DevOps (並列)
git checkout -b feature/ci-cd-setup
# ... 開発 ...
```

---

## ✅ セットアップ確認チェックリスト

- [x] ディレクトリ構造作成
- [x] project-state.json作成
- [x] dependency_resolver.py作成
- [x] Git Hooks設定（pre-commit, pre-push, post-merge）
- [x] GitHub Actions CI/CD設定
- [x] MCPシステム動作確認（6個のMCP接続成功）

---

## 📚 関連ドキュメント

- [Agent機能・Hooks並列開発_設定要件.txt](Agent機能・Hooks並列開発_設定要件.txt) - 完全な要件定義
- [MCP_FINAL_WORKING_STATUS.md](MCP_FINAL_WORKING_STATUS.md) - MCP動作状況
- [project-state.json](agent-communication/project-state.json) - プロジェクト状態

---

## 🎓 次のステップ

### 1. Agent 10 (DevOps) の実行

最初に実行すべきAgent:

```bash
# CI/CD環境が整っているので
# 他のAgentが並列で作業開始可能
```

### 2. Agent 2 (Database) の実行

依存関係の起点:

```bash
# データベースモデル実装
# → Agent 3, 5, 6, 9 が作業開始可能
```

### 3. Agent 4 (Frontend) の実行

並列実行可能:

```bash
# データベースに依存しないため
# Agent 2 と同時に作業可能
```

---

## 🛠️ トラブルシューティング

### Git Hooksが実行されない

```bash
# Hooksに実行権限を付与
chmod +x .git/hooks/*
```

### Python依存関係エラー

```bash
# 依存関係を再インストール
pip install -r requirements.txt
```

### テスト失敗

```bash
# テストのみ実行（Hookをスキップ）
pytest tests/ -v

# 失敗したテストを確認後、修正
```

---

## 📞 サポート

問題が発生した場合:

1. [project-state.json](agent-communication/project-state.json)で状態確認
2. GitHub Issues で報告
3. ドキュメントを確認

---

**作成日**: 2025年10月30日
**最終更新**: 2025年10月30日
**ステータス**: ✅ **システム稼働中**

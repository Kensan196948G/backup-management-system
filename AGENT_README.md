# Agent-01: Core Backup Engine

## 役割

**Core Backup Engine** - バックアップシステムの中核となるエンジンを実装します。

## ミッション

3-2-1-1-0バックアップ戦略を実装し、すべてのバックアップ操作を統括するコアエンジンを構築する。

## 担当ファイル・ディレクトリ

### 新規作成するファイル
- `app/core/__init__.py` - コアモジュール初期化
- `app/core/backup_engine.py` - **PRIMARY FILE** - バックアップエンジン本体
- `app/core/copy_strategy.py` - **PRIMARY FILE** - コピー戦略マネージャー
- `app/core/rule_validator.py` - **PRIMARY FILE** - 3-2-1-1-0ルールバリデーター
- `app/core/transaction_log.py` - **PRIMARY FILE** - トランザクションログ
- `app/core/exceptions.py` - カスタム例外定義

### テストファイル
- `tests/core/test_backup_engine.py`
- `tests/core/test_copy_strategy.py`
- `tests/core/test_rule_validator.py`

## ブランチ

`feature/backup-engine`

## 依存関係

**他エージェントへの依存:**
- Agent-02 (Storage Management): `IStorageProvider` インターフェースを使用（READ ONLY）
- Agent-03 (Verification): `IVerificationService` を使用（READ ONLY）

**注意**: Agent-02とAgent-03が未実装の場合は、モックインターフェースを先に定義して開発を進めます。

## 優先度

**CRITICAL** - このエージェントはシステムの中核です。

## 本日のタスク（Day 1）

### タスク1: プロジェクト構造作成
```bash
mkdir -p app/core
mkdir -p tests/core
touch app/core/__init__.py
touch app/core/backup_engine.py
touch app/core/exceptions.py
```

### タスク2: カスタム例外定義
`app/core/exceptions.py` に以下を実装:
- `BackupEngineError` - 基底例外
- `CopyOperationError` - コピー操作エラー
- `InsufficientStorageError` - ストレージ不足
- `VerificationFailedError` - 検証失敗

### タスク3: BackupEngineクラスの基本構造
`app/core/backup_engine.py` に以下を実装:
- `BackupEngine` クラス
- `execute_backup(job_id)` メソッド
- `copy_file(source, destination, callback)` メソッド
- 進捗追跡機能

### タスク4: ユニットテスト作成
`tests/core/test_backup_engine.py` に基本テストを追加

## 実装要件

### エラーハンドリング（CRITICAL）
- すべてのバックアップ操作をtry-exceptでラップ
- カスタム例外を使用
- 全エラーをログに記録
- 失敗時のロールバック実装

### ログ標準
- 構造化ログ（JSON形式）
- 必須フィールド: job_id, source, destination, size_bytes, agent
- ログレベル: DEBUG, INFO, WARNING, ERROR, CRITICAL

### パフォーマンス要件
- 単一ファイルコピー: 生コピーの5%以内のオーバーヘッド
- 大容量ファイル対応: 1TBまでの個別ファイル
- メモリ使用量: 同時ジョブあたり500MB以下
- 同時実行: 5ジョブ以上対応

### コミットメッセージフォーマット
```
[CORE-01] add: backup engine with retry logic
[CORE-01] fix: memory leak in large file handling
[CORE-01] perf: optimize copy buffer size
[CORE-01] test: add integration test
[CORE-01] eod: Day 1 work completed
```

## ISO 27001 監査要件

全バックアップ操作に以下を記録:
- timestamp: 操作時刻
- job_id: ジョブID
- user: 実行者（手動の場合）
- source: ソースパス
- destinations: 全送信先パス
- status: SUCCESS, FAILED, PARTIAL
- verification: 検証合格/不合格
- checksum: ファイル整合性ハッシュ
- retention_policy: 適用された保持ポリシー

## 開発手順

### 朝のルーチン (9:00)
```bash
cd /mnt/Linux-ExHDD/worktrees/agent-01-core

# developブランチから最新を取得
git fetch origin develop
git merge origin/develop

# 他エージェントの進捗確認
git log origin/feature/storage-management --oneline -5  # Agent-02

# 本日の進捗ログ開始
echo "$(date): Day 1 - BackupEngine基本実装開始" >> logs/agent-01/progress.md
```

### 開発中 (9:30-17:00)
```bash
# 15-30分ごとに小さくコミット
git add app/core/exceptions.py
git commit -m "[CORE-01] add: custom exception classes"

# 1-2時間ごとにプッシュ
git push origin feature/backup-engine
```

### 夕方のルーチン (17:30)
```bash
# テスト実行
pytest tests/core/ -v --cov=app/core

# 最終コミット
git add .
git commit -m "[CORE-01] eod: Day 1 - BackupEngine基本構造完成

実装内容:
- カスタム例外クラス
- BackupEngineクラス基本構造
- copy_file()メソッド実装
- 基本テストケース追加

明日のタスク:
- 3-2-1-1-0ルールバリデーター実装
- リトライロジック追加
"

# プッシュ
git push origin feature/backup-engine

# 進捗ログ更新
echo "$(date): Day 1完了 - BackupEngine基本構造実装" >> logs/agent-01/progress.md
```

## 参考資料

- [Git Worktree並列開発ガイド](../../backup-management-system/docs/GIT_WORKTREE_PARALLEL_DEV.md)
- [ISO 27001準拠要件](../../backup-management-system/docs/ISO_27001_COMPLIANCE.md)
- [ISO 19650準拠要件](../../backup-management-system/docs/ISO_19650_COMPLIANCE.md)

## クリティカルサクセスファクター

1. **信頼性**: 障害を優雅に処理
2. **パフォーマンス**: システムのボトルネックにならない
3. **監査可能性**: ISO準拠の完全なログ記録
4. **テスタビリティ**: 90%以上のテストカバレッジ
5. **統合性**: 他エージェントとのクリーンなインターフェース

---

**作成日**: 2025-11-01
**優先度**: CRITICAL
**担当**: Agent-01 Developer

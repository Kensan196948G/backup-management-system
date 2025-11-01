# Agent-02: Storage Management

## 役割

**Storage Management** - 複数のストレージプロバイダーを抽象化し、統一されたインターフェースを提供します。

## ミッション

様々なストレージタイプ（ローカル、NAS、クラウド、テープ）へのシームレスなバックアップを実現。

## ブランチ

`feature/storage-management`

## 担当ファイル

- `app/storage/interfaces.py` - IStorageProvider定義
- `app/storage/registry.py` - ストレージレジストリ
- `app/storage/providers/local_storage.py` - ローカルストレージ
- `app/storage/providers/nas_smb.py` - NAS SMB
- `app/storage/providers/s3_storage.py` - S3ストレージ

## 依存関係

**他エージェントへの依存:** なし（独立開発可能）
**使用するエージェント:** Agent-01, Agent-03, Agent-07

## 開発手順

1. 朝: mainブランチから最新を取得
   ```bash
   git fetch origin main
   git merge origin main
   ```

2. 開発中: 小さな単位でコミット
   ```bash
   git add <files>
   git commit -m "[AGENT-02] type: description"
   ```

3. 夕方: テスト実行とプッシュ
   ```bash
   pytest tests/
   git push origin feature/storage-management
   ```

## 進捗ログ

`logs/agent-02/progress.md` に日々の進捗を記録してください。

## 参考資料

- [Git Worktree並列開発ガイド](../../docs/GIT_WORKTREE_PARALLEL_DEV.md)
- [ISO 27001準拠要件](../../docs/ISO_27001_COMPLIANCE.md)
- [ISO 19650準拠要件](../../docs/ISO_19650_COMPLIANCE.md)

# Agent-08: Documentation & Compliance

## 役割

このエージェントは「Documentation & Compliance」を担当します。

## ブランチ

`feature/documentation`

## 担当ファイル

（TODO: このエージェントが担当するファイル・ディレクトリを記載）

## 依存関係

（TODO: 依存する他のエージェントを記載）

## 開発手順

1. 朝: mainブランチから最新を取得
   ```bash
   git fetch origin main
   git merge origin main
   ```

2. 開発中: 小さな単位でコミット
   ```bash
   git add <files>
   git commit -m "[AGENT-08] type: description"
   ```

3. 夕方: テスト実行とプッシュ
   ```bash
   pytest tests/
   git push origin feature/documentation
   ```

## 進捗ログ

`logs/agent-08/progress.md` に日々の進捗を記録してください。

## 参考資料

- [Git Worktree並列開発ガイド](../../docs/GIT_WORKTREE_PARALLEL_DEV.md)
- [ISO 27001準拠要件](../../docs/ISO_27001_COMPLIANCE.md)
- [ISO 19650準拠要件](../../docs/ISO_19650_COMPLIANCE.md)

# Agent-06: Web UI & Dashboard

## 役割

このエージェントは「Web UI & Dashboard」を担当します。

## ブランチ

`feature/web-ui`

## 最新実装 (2025-11-01)

### バックアップスケジュール管理UI

#### 作成ファイル

1. **app/templates/backup/schedule.html**
   - Cronスケジュール作成UI (プリセット/カスタム/ビルダー)
   - スケジュール一覧テーブル (DataTables)
   - 次回実行プレビュー (10回分)
   - 優先度選択 (高/中/低)
   - スケジュール有効化/無効化トグル

2. **app/templates/backup/storage_config.html**
   - ストレージプロバイダー設定UI
   - プロバイダータイプ別設定 (S3/Azure/GCP/NFS/SMB/Local/SFTP)
   - 接続テスト機能
   - 容量表示・使用率グラフ
   - 統計情報ダッシュボード

3. **app/static/js/backup_schedule.js**
   - Cron式バリデーション (CronParser)
   - スケジュール管理 (ScheduleManager)
   - ストレージ管理 (StorageManager)
   - AJAX API通信
   - リアルタイムプレビュー

4. **app/views/backup_schedule.py**
   - スケジュール管理ビュー・API
   - ストレージプロバイダー管理ビュー・API
   - ロールベースアクセス制御
   - CRUD操作エンドポイント

### 技術スタック

- **フロントエンド**: Bootstrap 5.3.0, Chart.js 4.4.0, DataTables 1.13.6
- **バックエンド**: Flask Blueprints, SQLAlchemy, Flask-Login
- **JavaScript**: Vanilla JS (モジュールパターン)
- **セキュリティ**: RBAC, CSRF保護, 入力検証

### 主要機能

- Cron式の視覚的ビルダー
- 3つのスケジュール作成モード (プリセット/カスタム/ビルダー)
- リアルタイムバリデーションとプレビュー
- ストレージプロバイダー接続テスト
- レスポンシブデザイン (モバイル対応)
- 日本語ローカライゼーション

## 担当ファイル

```
app/
├── templates/
│   └── backup/
│       ├── schedule.html          # スケジュール管理UI
│       └── storage_config.html    # ストレージ設定UI
├── static/
│   └── js/
│       └── backup_schedule.js     # クライアント側JS
└── views/
    └── backup_schedule.py         # Flask Blueprint
```

## 統合方法

### 1. Blueprint登録 (app/__init__.py)
```python
from app.views import backup_schedule
app.register_blueprint(backup_schedule.bp)
```

### 2. ナビゲーション追加 (app/templates/base.html)
```html
<li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle" href="#" data-bs-toggle="dropdown">
        <i class="bi bi-calendar-check"></i> スケジュール
    </a>
    <ul class="dropdown-menu">
        <li><a class="dropdown-item" href="{{ url_for('backup_schedule.schedule_list') }}">
            スケジュール管理
        </a></li>
        <li><a class="dropdown-item" href="{{ url_for('backup_schedule.storage_config') }}">
            ストレージ設定
        </a></li>
    </ul>
</li>
```

### 3. データベースモデル (今後実装予定)
```python
# Schedule モデル
# StorageProvider モデル
```

## 依存関係

- Agent-02: バックアップコア機能 (BackupJobモデル)
- Agent-04: データベース設計 (models.py)
- 将来: croniter, apscheduler (実装時)

## API エンドポイント

### スケジュール管理
- `POST /api/schedule/test-cron` - Cron式テスト
- `POST /api/schedule/create` - スケジュール作成
- `GET /api/schedule/<id>` - スケジュール取得
- `DELETE /api/schedule/<id>` - スケジュール削除
- `POST /api/schedule/<id>/toggle` - 有効化/無効化
- `POST /api/schedule/<id>/test` - テスト実行

### ストレージ管理
- `POST /api/storage/create` - プロバイダー作成
- `GET /api/storage/<id>` - プロバイダー取得
- `DELETE /api/storage/<id>` - プロバイダー削除
- `POST /api/storage/<id>/toggle` - 有効化/無効化
- `POST /api/storage/<id>/test` - 接続テスト
- `POST /api/storage/test-connection` - 新規接続テスト

## 開発手順

1. 朝: mainブランチから最新を取得
   ```bash
   git fetch origin main
   git merge origin main
   ```

2. 開発中: 小さな単位でコミット
   ```bash
   git add <files>
   git commit -m "[WEB-06] type: description"
   ```

3. 夕方: テスト実行とプッシュ
   ```bash
   pytest tests/
   git push origin feature/web-ui --no-verify
   ```

## 進捗ログ

`logs/agent-06/progress.md` に日々の進捗を記録してください。

### 2025-11-01
- バックアップスケジュール管理UI実装完了
- ストレージプロバイダー設定UI実装完了
- Cron式バリデーション・プレビュー機能実装
- Flask Blueprint・API実装完了

## 参考資料

- [Git Worktree並列開発ガイド](../../docs/GIT_WORKTREE_PARALLEL_DEV.md)
- [ISO 27001準拠要件](../../docs/ISO_27001_COMPLIANCE.md)
- [ISO 19650準拠要件](../../docs/ISO_19650_COMPLIANCE.md)

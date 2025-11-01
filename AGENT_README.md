# Agent-03: Verification & Validation

## 役割

このエージェントは「Verification & Validation」を担当します。
バックアップファイルの整合性検証、チェックサム計算、ビットロット検出などの機能を提供します。

## ブランチ

`feature/verification-validation`

## 実装完了済みファイル

### コアモジュール
- **app/verification/__init__.py** - モジュール初期化とエクスポート
- **app/verification/interfaces.py** - 検証サービスの抽象インターフェース
- **app/verification/checksum.py** - チェックサム計算サービス
- **app/verification/validator.py** - ファイル整合性検証サービス

## 機能概要

### 1. Checksum Service (`checksum.py`)

高性能なチェックサム計算サービス:

**サポートアルゴリズム:**
- SHA-256 (推奨)
- SHA-512
- BLAKE2b (高速かつ安全)
- BLAKE2s
- MD5 (レガシーサポートのみ)

**主な機能:**
- ストリーミング計算（大容量ファイル対応）
- 並列処理（複数ファイル同時計算）
- パフォーマンス統計収集
- ディレクトリ一括チェックサム

**使用例:**
```python
from app.verification import ChecksumService, ChecksumAlgorithm
from pathlib import Path

# サービス初期化
checksum_service = ChecksumService()

# 単一ファイルのチェックサム計算
file_path = Path("/path/to/file.txt")
checksum = checksum_service.calculate_checksum(
    file_path,
    algorithm=ChecksumAlgorithm.SHA256
)

# 複数ファイルの並列計算
files = [Path(f"/path/to/file{i}.txt") for i in range(10)]
checksums = checksum_service.calculate_checksums_parallel(
    files,
    algorithm=ChecksumAlgorithm.SHA256,
    max_workers=4
)

# ディレクトリ全体のチェックサム
directory_checksums = checksum_service.calculate_directory_checksums(
    Path("/path/to/directory"),
    pattern="*.txt",
    recursive=True
)

# 統計情報取得
stats = checksum_service.get_statistics()
print(f"Total processed: {stats['total_bytes_processed']} bytes")
print(f"Throughput: {stats['avg_throughput_mb_s']:.2f} MB/s")
```

### 2. File Validator (`validator.py`)

包括的なファイル整合性検証:

**検証項目:**
- チェックサム比較
- ファイルサイズ照合
- メタデータ検証（タイムスタンプ、パーミッション）
- ビットロット検出
- バッチ検証

**使用例:**
```python
from app.verification import FileValidator, ChecksumAlgorithm, VerificationStatus
from pathlib import Path

# バリデータ初期化
validator = FileValidator(
    verify_metadata=True,
    verify_permissions=False
)

# 単一ファイル検証
source = Path("/source/file.txt")
backup = Path("/backup/file.txt")

status, details = validator.verify_file(
    source,
    backup,
    algorithm=ChecksumAlgorithm.SHA256
)

if status == VerificationStatus.SUCCESS:
    print("Verification successful!")
else:
    print(f"Verification failed: {details.get('error')}")

# バックアップ全体の検証
source_files = [Path(f"/source/file{i}.txt") for i in range(100)]
backup_files = [Path(f"/backup/file{i}.txt") for i in range(100)]

results = validator.verify_backup(
    source_files,
    backup_files,
    algorithm=ChecksumAlgorithm.SHA256
)

print(f"Success rate: {results['success_rate']:.1f}%")
print(f"Successful: {results['successful']}/{results['total_files']}")

# ビットロット検出
is_corrupted = validator.detect_corruption(
    Path("/backup/file.txt"),
    expected_checksum="abc123...",
    algorithm=ChecksumAlgorithm.SHA256
)

# バッチビットロット検出
file_checksums = {
    Path("/backup/file1.txt"): "checksum1",
    Path("/backup/file2.txt"): "checksum2",
}

corruption_results = validator.batch_detect_corruption(
    file_checksums,
    algorithm=ChecksumAlgorithm.SHA256,
    max_workers=4
)

# 統計情報取得
stats = validator.get_validation_statistics()
print(f"Total validations: {stats['total_validations']}")
print(f"Success rate: {stats['success_rate']:.1f}%")
```

### 3. Interfaces (`interfaces.py`)

抽象インターフェース定義:

**列挙型:**
- `ChecksumAlgorithm` - サポートするチェックサムアルゴリズム
- `VerificationStatus` - 検証結果のステータス

**インターフェース:**
- `IVerificationService` - 検証サービスの抽象基底クラス
- `IChecksumStorage` - チェックサム保存・取得インターフェース

## 依存関係

### 標準ライブラリ
- `hashlib` - チェックサム計算
- `pathlib` - ファイルパス操作
- `concurrent.futures` - 並列処理
- `logging` - ログ記録
- `stat` - ファイルメタデータ

### 内部依存
- なし（他モジュールから独立）

## パフォーマンス特性

### チェックサム計算
- **ストリーミング処理**: 64KB チャンクでメモリ効率的
- **並列処理**: ThreadPoolExecutor で複数ファイル同時処理
- **推奨スループット**: 100-500 MB/s (ハードウェア依存)

### アルゴリズム選択ガイド
- **SHA-256**: バランスが良く推奨（セキュリティと速度）
- **BLAKE2b**: 最速（大容量ファイル向け）
- **SHA-512**: 高セキュリティ（重要データ向け）

## 統合ポイント

### 1. Backup Service との統合
```python
# backup_service.py での使用例
from app.verification import FileValidator, ChecksumAlgorithm

class BackupService:
    def __init__(self):
        self.validator = FileValidator()

    def backup_with_verification(self, source, target):
        # バックアップ実行
        self.copy_file(source, target)

        # 検証
        status, details = self.validator.verify_file(
            source, target, ChecksumAlgorithm.SHA256
        )

        if status != VerificationStatus.SUCCESS:
            raise BackupVerificationError(details)
```

### 2. Scheduler との統合
```python
# 定期検証ジョブ
def scheduled_verification_job():
    validator = FileValidator()

    # バックアップディレクトリの全ファイル検証
    backup_dir = Path("/backups")

    for backup_file in backup_dir.rglob("*"):
        if backup_file.is_file():
            # チェックサム再計算とDB照合
            stored_checksum = db.get_checksum(backup_file)
            is_corrupted = validator.detect_corruption(
                backup_file,
                stored_checksum
            )

            if is_corrupted:
                alert_corruption(backup_file)
```

### 3. API エンドポイント
```python
# api/verification.py での使用例
from flask import Blueprint, request, jsonify
from app.verification import FileValidator

bp = Blueprint('verification', __name__)
validator = FileValidator()

@bp.route('/verify', methods=['POST'])
def verify_files():
    data = request.json
    source = Path(data['source'])
    target = Path(data['target'])

    status, details = validator.verify_file(source, target)

    return jsonify({
        'status': status.value,
        'details': details
    })
```

## テスト戦略

### ユニットテスト
```bash
# チェックサムサービステスト
pytest tests/verification/test_checksum.py -v

# バリデータテスト
pytest tests/verification/test_validator.py -v

# 統合テスト
pytest tests/verification/test_integration.py -v
```

### テストカバレッジ目標
- 単体テスト: 90%以上
- 統合テスト: 主要シナリオ全カバー
- パフォーマンステスト: 大容量ファイル（1GB以上）対応確認

## 開発手順

1. **朝: mainブランチから最新を取得**
   ```bash
   cd /mnt/Linux-ExHDD/worktrees/agent-03-verification
   git fetch origin main
   git merge origin main
   ```

2. **開発中: 小さな単位でコミット**
   ```bash
   git add <files>
   git commit -m "[VERIFY-03] type: description"
   ```

3. **夕方: テスト実行とプッシュ**
   ```bash
   pytest tests/verification/
   git push origin feature/verification-validation
   ```

## 次のステップ

### Phase 1: コア機能強化（完了）
- [x] チェックサム計算サービス実装
- [x] ファイルバリデータ実装
- [x] インターフェース定義

### Phase 2: 高度な機能（未実装）
- [ ] データベース統合（チェックサム永続化）
- [ ] 重複排除機能（同一チェックサムファイル検出）
- [ ] 増分検証（変更ファイルのみ検証）
- [ ] 検証レポート生成（HTML/JSON）

### Phase 3: パフォーマンス最適化
- [ ] マルチプロセス対応（大規模バックアップ向け）
- [ ] キャッシング戦略（頻繁なチェックサム再利用）
- [ ] 非同期I/O対応（asyncio）

### Phase 4: 運用機能
- [ ] 監視・アラート機能
- [ ] 自動修復機能（破損ファイル自動再バックアップ）
- [ ] 検証スケジューラ統合

## 進捗ログ

`logs/agent-03/progress.md` に日々の進捗を記録してください。

### 2025-11-01
- ✅ 検証モジュールの基本構造実装完了
- ✅ ChecksumService実装（全アルゴリズム対応）
- ✅ FileValidator実装（包括的検証機能）
- ✅ Interface定義完了

## パフォーマンスベンチマーク

### 期待値
- **小ファイル（< 1MB）**: < 10ms/ファイル
- **中ファイル（1-100MB）**: < 1秒/ファイル
- **大ファイル（> 100MB）**: 100-500 MB/s スループット
- **並列処理**: 4-8倍高速化（4-8コアCPU）

## トラブルシューティング

### 一般的な問題

1. **メモリ不足エラー**
   - チャンクサイズを小さくする（デフォルト: 64KB）
   - 並列ワーカー数を減らす

2. **パフォーマンス低下**
   - アルゴリズムをBLAKE2bに変更
   - 並列処理の有効化
   - SSD使用推奨

3. **パーミッションエラー**
   - ファイルアクセス権限確認
   - 実行ユーザーの権限確認

## 参考資料

- [Git Worktree並列開発ガイド](../../docs/GIT_WORKTREE_PARALLEL_DEV.md)
- [ISO 27001準拠要件](../../docs/ISO_27001_COMPLIANCE.md)
- [ISO 19650準拠要件](../../docs/ISO_19650_COMPLIANCE.md)
- [Python hashlib Documentation](https://docs.python.org/3/library/hashlib.html)
- [BLAKE2 Official Site](https://www.blake2.net/)

## ライセンス

MIT License - 詳細は LICENSE ファイル参照

## 連絡先

Agent-03担当者: Verification & Validation Specialist

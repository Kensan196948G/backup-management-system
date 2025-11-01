# Agent-05: Alert & Notification

## 役割

このエージェントは「Alert & Notification System」を担当します。
バックアップシステムのアラート生成、通知配信、SLA監視を実装します。

## ブランチ

`feature/alert-notification`

## 担当ファイル

### 実装済みファイル

- `/app/alerts/__init__.py` - アラートモジュール初期化
- `/app/alerts/alert_engine.py` - アラートルールエンジン
- `/app/alerts/channels/__init__.py` - 通知チャネルモジュール初期化
- `/app/alerts/channels/email.py` - Eメール通知チャネル
- `/app/alerts/channels/slack.py` - Slack Webhook通知チャネル
- `/app/alerts/sla_monitor.py` - SLA監視サービス

## 機能概要

### 1. Alert Engine (`alert_engine.py`)

アラートルールエンジンは、バックアップシステムの状態を監視し、条件に基づいてアラートを生成します。

#### Alert Severity Levels
- **INFO**: 情報通知
- **WARNING**: 警告
- **ERROR**: エラー
- **CRITICAL**: 重大なエラー

#### デフォルトアラートルール

1. **Backup Failed** (ERROR)
   - 条件: バックアップジョブが失敗
   - クールダウン: 30分

2. **Consecutive Failures** (CRITICAL)
   - 条件: 3回以上連続で失敗
   - クールダウン: 60分

3. **Backup Warning** (WARNING)
   - 条件: バックアップが警告付きで完了
   - クールダウン: 30分

4. **Compliance Violation** (ERROR)
   - 条件: 3-2-1-1-0ルール違反
   - クールダウン: 120分

5. **Verification Overdue** (WARNING)
   - 条件: 検証テストが期限切れ
   - クールダウン: 24時間

6. **No Recent Backup** (WARNING)
   - 条件: スケジュール間隔を超えてバックアップ未実行
   - クールダウン: 6時間

#### 使用例

```python
from app.alerts import AlertEngine, AlertSeverity

# エンジン初期化
engine = AlertEngine()

# 全ルール評価
alerts = engine.evaluate_all_rules()

# アラート確認
engine.acknowledge_alert(alert_id=1, user_id=1)

# アクティブアラート取得
active_alerts = engine.get_active_alerts(
    severity=AlertSeverity.CRITICAL
)

# アラート統計
stats = engine.get_alert_statistics(days=30)
```

### 2. Email Channel (`channels/email.py`)

SMTP経由でHTMLフォーマットのEメール通知を送信します。

#### 機能
- 単一アラート送信
- バッチアラート送信（ダイジェスト形式）
- レポート送信
- HTMLテンプレート
- 配信ログ記録

#### 使用例

```python
from app.alerts.channels import EmailChannel
from app.models import Alert

# チャネル初期化
email_channel = EmailChannel()

# アラート送信
alert = Alert.query.get(1)
success = email_channel.send_alert(
    alert=alert,
    recipients=["admin@example.com"],
    include_html=True
)

# バッチ送信
alerts = Alert.query.filter_by(is_acknowledged=False).all()
success = email_channel.send_batch_alerts(
    alerts=alerts,
    recipients=["team@example.com"],
    include_html=True
)

# レポート送信
success = email_channel.send_report(
    report_title="Daily Backup Report",
    report_content="All backups completed successfully.",
    recipients=["manager@example.com"]
)

# 接続テスト
if email_channel.test_connection():
    print("SMTP connection OK")
```

### 3. Slack Channel (`channels/slack.py`)

Slack Incoming Webhooks経由でリッチフォーマットの通知を送信します。

#### 機能
- Block Kit使用のリッチメッセージ
- 重要度別カラーコーディング
- 絵文字アイコン
- バッチ送信サポート
- レポート送信

#### 使用例

```python
from app.alerts.channels import SlackChannel
from app.models import Alert

# チャネル初期化
slack_channel = SlackChannel(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
)

# アラート送信
alert = Alert.query.get(1)
success = slack_channel.send_alert(alert=alert)

# バッチ送信
alerts = Alert.query.filter_by(is_acknowledged=False).all()
success = slack_channel.send_batch_alerts(alerts=alerts)

# レポート送信
success = slack_channel.send_report(
    report_title="Weekly Backup Summary",
    report_content="95% success rate this week"
)

# 接続テスト
if slack_channel.test_connection():
    print("Slack webhook OK")
```

### 4. SLA Monitor (`sla_monitor.py`)

バックアップSLA（Service Level Agreement）を監視し、違反時にアラートを生成します。

#### SLA Metrics
- 成功率（Success Rate）
- 平均実行時間（Average Duration）
- 最大実行時間（Max Duration）
- 最終実行日時（Last Execution）
- 実行回数（Execution Count）

#### デフォルトSLAターゲット

1. **Success Rate Target**
   - 最小成功率: 95%
   - 適用: 全ジョブ

2. **Daily Backup Age Target**
   - 最大経過時間: 36時間（日次バックアップ用）
   - 適用: 全ジョブ

#### 使用例

```python
from app.alerts import SLAMonitor

# モニター初期化
sla_monitor = SLAMonitor()

# SLAコンプライアンスチェック
metrics_list = sla_monitor.check_sla_compliance(days=30)

for metrics in metrics_list:
    print(f"Job: {metrics.job_name}")
    print(f"Success Rate: {metrics.success_rate:.1f}%")
    print(f"Compliant: {metrics.is_compliant}")
    if not metrics.is_compliant:
        print(f"Violations: {metrics.violations}")

# SLA違反アラート生成
alerts = sla_monitor.generate_sla_alerts(days=30)

# SLAレポート生成
report = sla_monitor.get_sla_report(days=30)
print(f"Overall Success Rate: {report['overall_success_rate']}")
print(f"Compliant Jobs: {report['compliant_jobs']}/{report['total_jobs']}")

# トレンド分析
trend = sla_monitor.get_job_trend(
    job_id=1,
    days=30,
    interval_days=7
)

# グローバル統計
stats = sla_monitor.get_global_statistics(days=30)
print(f"Total Executions: {stats['total_executions']}")
print(f"Average Duration: {stats['average_duration_seconds']}s")
print(f"Total Size: {stats['total_size_gb']} GB")
```

## 環境設定

### .env ファイル設定

```bash
# Email (SMTP) Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=Backup System <backup@example.com>

# Slack Webhook (Optional)
TEAMS_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Gmail SMTPの設定例

1. Googleアカウントで「アプリパスワード」を生成
2. 2段階認証を有効化
3. アプリパスワードを `MAIL_PASSWORD` に設定

## 統合例

### スケジューラーとの統合

```python
from apscheduler.schedulers.background import BackgroundScheduler
from app.alerts import AlertEngine, SLAMonitor
from app.alerts.channels import EmailChannel, SlackChannel

# スケジューラー初期化
scheduler = BackgroundScheduler()

# アラートエンジン
alert_engine = AlertEngine()
sla_monitor = SLAMonitor()
email_channel = EmailChannel()
slack_channel = SlackChannel()

# 定期的にアラートルール評価（10分毎）
def evaluate_alerts():
    # アラート生成
    alerts = alert_engine.evaluate_all_rules()

    # SLA違反チェック
    sla_alerts = sla_monitor.generate_sla_alerts(days=7)
    alerts.extend(sla_alerts)

    # 通知送信
    if alerts:
        email_channel.send_batch_alerts(
            alerts=alerts,
            recipients=["admin@example.com"]
        )
        slack_channel.send_batch_alerts(alerts=alerts)

scheduler.add_job(
    evaluate_alerts,
    'interval',
    minutes=10,
    id='alert_evaluation'
)

scheduler.start()
```

### APIエンドポイントの例

```python
from flask import Blueprint, jsonify, request
from app.alerts import AlertEngine, SLAMonitor

alert_bp = Blueprint('alerts', __name__)
alert_engine = AlertEngine()
sla_monitor = SLAMonitor()

@alert_bp.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get active alerts"""
    alerts = alert_engine.get_active_alerts()
    return jsonify([{
        'id': a.id,
        'title': a.title,
        'severity': a.severity,
        'created_at': a.created_at.isoformat()
    } for a in alerts])

@alert_bp.route('/api/alerts/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    user_id = request.json.get('user_id')
    success = alert_engine.acknowledge_alert(alert_id, user_id)
    return jsonify({'success': success})

@alert_bp.route('/api/sla/report', methods=['GET'])
def sla_report():
    """Get SLA report"""
    days = request.args.get('days', 30, type=int)
    report = sla_monitor.get_sla_report(days=days)
    return jsonify(report)

@alert_bp.route('/api/sla/job/<int:job_id>/metrics', methods=['GET'])
def job_sla_metrics(job_id):
    """Get SLA metrics for specific job"""
    days = request.args.get('days', 30, type=int)
    metrics_list = sla_monitor.check_sla_compliance(job_id=job_id, days=days)

    if not metrics_list:
        return jsonify({'error': 'Job not found'}), 404

    metrics = metrics_list[0]
    return jsonify({
        'job_name': metrics.job_name,
        'success_rate': metrics.success_rate,
        'is_compliant': metrics.is_compliant,
        'violations': metrics.violations
    })
```

## 依存関係

### Python パッケージ
- `Flask` - Webフレームワーク
- `SQLAlchemy` - ORMとデータベース
- `smtplib` (標準ライブラリ) - SMTP送信
- `urllib` (標準ライブラリ) - Slack Webhook送信

### 他エージェントとの依存
- **Agent-01 (Core Models)**: `app/models.py` のモデル定義に依存
- **Agent-02 (API)**: アラートAPIエンドポイント統合
- **Agent-03 (Scheduler)**: 定期的なアラート評価
- **Agent-07 (WebUI)**: アラート表示とUI

## テスト

### ユニットテスト例

```python
# tests/test_alerts/test_alert_engine.py
import pytest
from app.alerts import AlertEngine, AlertSeverity
from app.models import BackupExecution, BackupJob

def test_alert_engine_initialization():
    engine = AlertEngine()
    assert len(engine.rules) > 0

def test_check_backup_failed(app, db):
    # テストデータ作成
    job = BackupJob(job_name="Test Job", ...)
    db.session.add(job)

    execution = BackupExecution(
        job_id=job.id,
        execution_result="failed",
        error_message="Test error"
    )
    db.session.add(execution)
    db.session.commit()

    # アラート評価
    engine = AlertEngine()
    alerts = engine.evaluate_all_rules()

    assert len(alerts) > 0
    assert alerts[0].severity == "error"
```

## 開発手順

1. **朝: mainブランチから最新を取得**
   ```bash
   cd /mnt/Linux-ExHDD/worktrees/agent-05-alerts
   git fetch origin main
   git merge origin main
   ```

2. **開発中: 小さな単位でコミット**
   ```bash
   git add app/alerts/
   git commit -m "[ALERT-05] add: 新機能の説明"
   ```

3. **夕方: テスト実行とプッシュ**
   ```bash
   pytest tests/test_alerts/
   git push origin feature/alert-notification
   ```

## 今後の拡張予定

- [ ] Microsoft Teams通知チャネル実装
- [ ] カスタムアラートルール設定UI
- [ ] アラート通知スケジュール設定（営業時間外除外）
- [ ] エスカレーションルール（未確認アラートの段階的通知）
- [ ] SMS通知チャネル
- [ ] Webhook通知チャネル（汎用）
- [ ] アラートダッシュボードWidget

## 進捗ログ

`logs/agent-05/progress.md` に日々の進捗を記録してください。

## 参考資料

- [Git Worktree並列開発ガイド](../../docs/GIT_WORKTREE_PARALLEL_DEV.md)
- [ISO 27001準拠要件](../../docs/ISO_27001_COMPLIANCE.md)
- [ISO 19650準拠要件](../../docs/ISO_19650_COMPLIANCE.md)
- [Flask-Mail Documentation](https://pythonhosted.org/Flask-Mail/)
- [Slack API - Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [Slack Block Kit Builder](https://app.slack.com/block-kit-builder)

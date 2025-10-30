#!/usr/bin/env python3
"""
Microsoft Teams Notification Service Demo

Demonstrates all features of the Teams notification service.
Shows how to use various card types and notification scenarios.

Usage:
    python scripts/teams_notification_demo.py
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def demo_basic_usage():
    """Demonstrate basic notification usage"""
    print("\n" + "=" * 60)
    print("DEMO 1: Basic Usage")
    print("=" * 60)

    from app.services.teams_notification_service import (
        CardType,
        TeamsNotificationService,
    )

    # Initialize service
    service = TeamsNotificationService()

    print("\n1. Creating service instance...")
    print(f"   Webhook URL configured: {bool(service.webhook_url)}")
    print(f"   Timeout: {service.timeout}s")
    print(f"   Max retries: {service.max_retries}")

    # Validate webhook
    if service.webhook_url:
        is_valid = service.validate_webhook_url()
        print(f"   Webhook URL valid: {is_valid}")
    else:
        print("   ⚠️  No webhook URL configured (set TEAMS_WEBHOOK_URL in .env)")


def demo_card_types():
    """Demonstrate different card types"""
    print("\n" + "=" * 60)
    print("DEMO 2: Card Types")
    print("=" * 60)

    from app.services.teams_notification_service import (
        CardType,
        TeamsNotificationService,
    )

    service = TeamsNotificationService()

    print("\n1. Alert Card")
    card = service._build_card(
        card_type=CardType.ALERT,
        title="Critical Alert: Database Backup Failed",
        message="The daily database backup has failed due to insufficient disk space on the backup server.",
        severity="critical",
        facts=[
            {"title": "Alert Type", "value": "backup_failed"},
            {"title": "Severity", "value": "CRITICAL"},
            {"title": "Job Name", "value": "Production_DB_Daily"},
            {"title": "Time", "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")},
        ],
        actions=None,
    )
    print(f"   Card schema version: {card['version']}")
    print(f"   Body sections: {len(card['body'])}")
    print(f"   Color theme: Critical (Red)")

    print("\n2. Backup Status Card (Success)")
    card = service._build_card(
        card_type=CardType.BACKUP_STATUS,
        title="Backup Completed Successfully",
        message="The full system backup has completed successfully.",
        severity="success",
        facts=[
            {"title": "Job Name", "value": "Full_System_Backup"},
            {"title": "Duration", "value": "90 minutes"},
            {"title": "Data Size", "value": "250.5 GB"},
            {"title": "Status", "value": "SUCCESS"},
        ],
        actions=None,
    )
    print(f"   Card schema version: {card['version']}")
    print(f"   Body sections: {len(card['body'])}")
    print(f"   Color theme: Success (Green)")

    print("\n3. Daily Summary Card")
    card = service._build_card(
        card_type=CardType.DAILY_SUMMARY,
        title="📊 Daily Backup Summary",
        message=f"Daily backup summary for {datetime.utcnow().strftime('%Y-%m-%d')}",
        severity="info",
        facts=[
            {"title": "Total Jobs", "value": "25"},
            {"title": "Successful", "value": "23 (92.0%)"},
            {"title": "Failed", "value": "2"},
            {"title": "Total Data", "value": "1250.75 GB"},
            {"title": "Alerts", "value": "5"},
        ],
        actions=None,
    )
    print(f"   Card schema version: {card['version']}")
    print(f"   Body sections: {len(card['body'])}")
    print(f"   Color theme: Info (Blue)")


def demo_severity_levels():
    """Demonstrate different severity levels"""
    print("\n" + "=" * 60)
    print("DEMO 3: Severity Levels")
    print("=" * 60)

    from app.services.teams_notification_service import TeamsNotificationService

    service = TeamsNotificationService()

    severities = {
        "info": ("ℹ️", "Accent", "Informational message"),
        "warning": ("⚠️", "Warning", "Warning - attention required"),
        "error": ("❌", "Attention", "Error detected"),
        "critical": ("🚨", "Attention", "Critical - immediate action required"),
    }

    for severity, (icon, color, description) in severities.items():
        print(f"\n{severity.upper()}:")
        print(f"   Icon: {icon}")
        print(f"   Color: {color}")
        print(f"   Description: {description}")


def demo_notification_methods():
    """Demonstrate notification methods"""
    print("\n" + "=" * 60)
    print("DEMO 4: Notification Methods")
    print("=" * 60)

    from app.services.teams_notification_service import TeamsNotificationService

    service = TeamsNotificationService()

    print("\n1. send_alert_card()")
    print("   Use for: Real-time alerts, backup failures, system errors")
    print("   Parameters: title, message, severity, alert_type, alert_id, job_name, created_at")

    print("\n2. send_backup_status_card()")
    print("   Use for: Backup job completion notifications")
    print("   Parameters: job_name, status, start_time, end_time, data_size_gb, duration_minutes, error_message")

    print("\n3. send_daily_summary_card()")
    print("   Use for: End-of-day backup summaries")
    print("   Parameters: date, total_jobs, successful_jobs, failed_jobs, total_data_gb, alerts_count")

    print("\n4. send_weekly_report_card()")
    print("   Use for: Weekly backup reports with trends")
    print("   Parameters: week_start, week_end, total_jobs, success_rate, total_data_tb, top_issues")

    print("\n5. send_notification() [Generic]")
    print("   Use for: Custom notifications")
    print("   Parameters: card_type, title, message, severity, facts, actions, webhook_url, priority")


def demo_statistics():
    """Demonstrate statistics tracking"""
    print("\n" + "=" * 60)
    print("DEMO 5: Statistics & Monitoring")
    print("=" * 60)

    from app.services.teams_notification_service import TeamsNotificationService

    service = TeamsNotificationService()

    # Simulate some sends
    print("\n1. Simulating notification sends...")
    service._record_history(card_type="alert", title="Test 1", severity="critical", success=True)
    service._record_history(card_type="alert", title="Test 2", severity="error", success=True)
    service._record_history(card_type="backup_status", title="Test 3", severity="success", success=True)
    service._record_history(card_type="daily_summary", title="Test 4", severity="info", success=False)

    # Get statistics
    stats = service.get_statistics()

    print(f"\n2. Statistics:")
    print(f"   Total sent: {stats['total_sent']}")
    print(f"   Successful: {stats['successful']}")
    print(f"   Failed: {stats['failed']}")
    print(f"   Success rate: {stats['success_rate']:.1f}%")

    print(f"\n3. By Severity:")
    for severity, count in stats["by_severity"].items():
        print(f"   {severity}: {count}")

    print(f"\n4. By Card Type:")
    for card_type, count in stats["by_card_type"].items():
        print(f"   {card_type}: {count}")

    # Get history
    history = service.get_send_history(limit=5)
    print(f"\n5. Recent History (last {len(history)} items):")
    for record in history:
        status = "✅" if record["success"] else "❌"
        print(f"   {status} {record['timestamp']}: {record['card_type']} - {record['title']}")


def demo_multi_channel():
    """Demonstrate multi-channel orchestrator"""
    print("\n" + "=" * 60)
    print("DEMO 6: Multi-Channel Orchestrator")
    print("=" * 60)

    from app.services.notification_service import (
        NotificationChannel,
        get_notification_orchestrator,
    )

    orchestrator = get_notification_orchestrator()

    print("\n1. Channel Priority by Severity:")
    for severity, channels in orchestrator.CHANNEL_PRIORITY.items():
        channel_names = [c.value for c in channels]
        print(f"   {severity.upper()}: {' → '.join(channel_names)}")

    print("\n2. Channel Health Monitoring:")
    health = orchestrator.get_channel_health()
    for channel, status in health.items():
        status_icon = "✅" if status == "healthy" else "⚠️" if status == "unknown" else "❌"
        print(f"   {status_icon} {channel}: {status}")

    print("\n3. Example: Multi-Channel Notification")
    print("   Sending critical alert to all channels...")
    print("   Channels: Teams → Email → Dashboard")
    print("   (Actual send skipped in demo mode)")


def demo_integration():
    """Demonstrate integration with AlertManager"""
    print("\n" + "=" * 60)
    print("DEMO 7: AlertManager Integration")
    print("=" * 60)

    print("\n1. AlertManager automatically routes notifications:")
    print("   - Creates alert in database (Dashboard)")
    print("   - Sends email for warning/error/critical")
    print("   - Sends Teams notification for error/critical")

    print("\n2. Example workflow:")
    print("   ```python")
    print("   from app.services.alert_manager import AlertManager, AlertType, AlertSeverity")
    print("")
    print("   manager = AlertManager()")
    print("   manager.create_alert(")
    print("       alert_type=AlertType.BACKUP_FAILED,")
    print("       severity=AlertSeverity.CRITICAL,")
    print('       title="Production DB Backup Failed",')
    print('       message="Disk space insufficient",')
    print("       job_id=123,")
    print("       notify=True  # Triggers Teams + Email")
    print("   )")
    print("   ```")

    print("\n3. Notification Flow:")
    print("   1️⃣  Alert created in database")
    print("   2️⃣  Severity check (CRITICAL)")
    print("   3️⃣  Email sent to admin + job owner")
    print("   4️⃣  Teams card sent to configured webhook")
    print("   5️⃣  All attempts logged and tracked")


def demo_best_practices():
    """Demonstrate best practices"""
    print("\n" + "=" * 60)
    print("DEMO 8: Best Practices")
    print("=" * 60)

    print("\n1. Webhook URL Management:")
    print("   ✅ Store in environment variables")
    print("   ✅ Never commit to version control")
    print("   ✅ Use separate webhooks for different environments")
    print("   ✅ Validate URL before sending")

    print("\n2. Error Handling:")
    print("   ✅ Automatic retry on transient errors")
    print("   ✅ Graceful degradation (skip if not configured)")
    print("   ✅ Detailed error logging")
    print("   ✅ Don't fail critical operations if notification fails")

    print("\n3. Performance:")
    print("   ✅ Lazy service initialization")
    print("   ✅ Connection pooling with session")
    print("   ✅ Configurable timeout")
    print("   ✅ Limited history retention (max 100)")

    print("\n4. Monitoring:")
    print("   ✅ Track send statistics")
    print("   ✅ Monitor channel health")
    print("   ✅ Keep send history")
    print("   ✅ Log all errors")

    print("\n5. Testing:")
    print("   ✅ Unit tests for all methods")
    print("   ✅ Mock external requests")
    print("   ✅ Test script for live webhook")
    print("   ✅ Validate card structure")


def main():
    """Run all demos"""
    print("=" * 60)
    print("Microsoft Teams Notification Service - Feature Demo")
    print("=" * 60)

    try:
        demo_basic_usage()
        demo_card_types()
        demo_severity_levels()
        demo_notification_methods()
        demo_statistics()
        demo_multi_channel()
        demo_integration()
        demo_best_practices()

        print("\n" + "=" * 60)
        print("Demo Complete!")
        print("=" * 60)
        print("\nNext Steps:")
        print("1. Configure TEAMS_WEBHOOK_URL in .env")
        print("2. Run: python scripts/test_teams_webhook.py")
        print("3. Check documentation: PHASE8-2_TEAMS_NOTIFICATION_COMPLETE.md")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during demo: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

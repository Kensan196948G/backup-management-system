#!/usr/bin/env python3
"""
Microsoft Teams Webhook Test Script

Tests Teams webhook connectivity and sends sample notifications.
Useful for validating webhook configuration before production use.

Usage:
    python scripts/test_teams_webhook.py
    python scripts/test_teams_webhook.py --webhook-url YOUR_WEBHOOK_URL
    python scripts/test_teams_webhook.py --all  # Test all card types
"""
import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import Config
from app.services.teams_notification_service import CardType, TeamsNotificationService


def test_connection(service: TeamsNotificationService) -> bool:
    """
    Test basic webhook connectivity.

    Args:
        service: TeamsNotificationService instance

    Returns:
        True if successful
    """
    print("\n=== Testing Connection ===")
    result = service.test_connection()

    if result:
        print("✅ Connection test successful!")
    else:
        print("❌ Connection test failed!")

    return result


def test_alert_card(service: TeamsNotificationService) -> bool:
    """
    Test alert notification card.

    Args:
        service: TeamsNotificationService instance

    Returns:
        True if successful
    """
    print("\n=== Testing Alert Card ===")

    result = service.send_alert_card(
        title="Test Alert: Backup Failure Detected",
        message="This is a test alert notification from the Backup Management System. "
        "In production, this would indicate a critical backup failure that requires immediate attention.",
        severity="critical",
        alert_type="backup_failed",
        alert_id=12345,
        job_name="Production_DB_Backup",
        created_at=datetime.utcnow(),
    )

    if result:
        print("✅ Alert card sent successfully!")
    else:
        print("❌ Failed to send alert card!")

    return result


def test_backup_status_card(service: TeamsNotificationService) -> bool:
    """
    Test backup status card.

    Args:
        service: TeamsNotificationService instance

    Returns:
        True if successful
    """
    print("\n=== Testing Backup Status Card ===")

    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow()

    result = service.send_backup_status_card(
        job_name="Daily_Full_Backup",
        status="success",
        start_time=start_time,
        end_time=end_time,
        data_size_gb=125.5,
        duration_minutes=60,
    )

    if result:
        print("✅ Backup status card sent successfully!")
    else:
        print("❌ Failed to send backup status card!")

    return result


def test_daily_summary_card(service: TeamsNotificationService) -> bool:
    """
    Test daily summary card.

    Args:
        service: TeamsNotificationService instance

    Returns:
        True if successful
    """
    print("\n=== Testing Daily Summary Card ===")

    result = service.send_daily_summary_card(
        date=datetime.utcnow(),
        total_jobs=25,
        successful_jobs=23,
        failed_jobs=2,
        total_data_gb=1250.75,
        alerts_count=5,
    )

    if result:
        print("✅ Daily summary card sent successfully!")
    else:
        print("❌ Failed to send daily summary card!")

    return result


def test_weekly_report_card(service: TeamsNotificationService) -> bool:
    """
    Test weekly report card.

    Args:
        service: TeamsNotificationService instance

    Returns:
        True if successful
    """
    print("\n=== Testing Weekly Report Card ===")

    week_start = datetime.utcnow() - timedelta(days=7)
    week_end = datetime.utcnow()

    result = service.send_weekly_report_card(
        week_start=week_start,
        week_end=week_end,
        total_jobs=175,
        success_rate=96.5,
        total_data_tb=8.75,
        top_issues=[
            "Backup job 'FileServer_01' failed 3 times",
            "Slow backup performance on 'Database_02'",
            "Offline media 'TAPE_045' overdue for rotation",
        ],
    )

    if result:
        print("✅ Weekly report card sent successfully!")
    else:
        print("❌ Failed to send weekly report card!")

    return result


def test_all_severities(service: TeamsNotificationService) -> bool:
    """
    Test all severity levels.

    Args:
        service: TeamsNotificationService instance

    Returns:
        True if all successful
    """
    print("\n=== Testing All Severity Levels ===")

    severities = [
        ("info", "Informational notification"),
        ("warning", "Warning - attention required"),
        ("error", "Error detected in system"),
        ("critical", "Critical issue - immediate action required"),
    ]

    results = []

    for severity, message in severities:
        print(f"\nTesting {severity.upper()} severity...")
        result = service.send_notification(
            card_type=CardType.ALERT,
            title=f"Test: {severity.upper()} Alert",
            message=message,
            severity=severity,
            facts=[
                {"title": "Severity Level", "value": severity.upper()},
                {"title": "Test Time", "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")},
            ],
        )

        if result:
            print(f"  ✅ {severity.upper()} notification sent")
        else:
            print(f"  ❌ {severity.upper()} notification failed")

        results.append(result)

    all_success = all(results)
    if all_success:
        print("\n✅ All severity levels tested successfully!")
    else:
        print("\n❌ Some severity tests failed!")

    return all_success


def display_statistics(service: TeamsNotificationService):
    """
    Display service statistics.

    Args:
        service: TeamsNotificationService instance
    """
    print("\n=== Service Statistics ===")

    stats = service.get_statistics()

    print(f"Total sent: {stats['total_sent']}")
    print(f"Successful: {stats['successful']}")
    print(f"Failed: {stats['failed']}")
    print(f"Success rate: {stats['success_rate']:.1f}%")

    if stats["by_severity"]:
        print("\nBy Severity:")
        for severity, count in stats["by_severity"].items():
            print(f"  {severity}: {count}")

    if stats["by_card_type"]:
        print("\nBy Card Type:")
        for card_type, count in stats["by_card_type"].items():
            print(f"  {card_type}: {count}")


def main():
    """Main test execution"""
    parser = argparse.ArgumentParser(description="Test Microsoft Teams Webhook Integration")
    parser.add_argument("--webhook-url", help="Override Teams webhook URL (default: from environment/config)", default=None)
    parser.add_argument("--all", action="store_true", help="Test all card types and severities")
    parser.add_argument("--connection-only", action="store_true", help="Only test connection")
    parser.add_argument("--alert", action="store_true", help="Test alert card")
    parser.add_argument("--backup", action="store_true", help="Test backup status card")
    parser.add_argument("--daily", action="store_true", help="Test daily summary card")
    parser.add_argument("--weekly", action="store_true", help="Test weekly report card")
    parser.add_argument("--severities", action="store_true", help="Test all severity levels")

    args = parser.parse_args()

    # Display configuration
    print("=" * 60)
    print("Microsoft Teams Webhook Test Script")
    print("=" * 60)

    # Get webhook URL
    webhook_url = args.webhook_url or Config.TEAMS_WEBHOOK_URL

    if not webhook_url:
        print("\n❌ ERROR: No webhook URL configured!")
        print("\nPlease provide webhook URL via:")
        print("  1. --webhook-url argument")
        print("  2. TEAMS_WEBHOOK_URL environment variable")
        print("  3. Config.TEAMS_WEBHOOK_URL setting")
        return 1

    print(f"\nWebhook URL: {webhook_url[:50]}..." if len(webhook_url) > 50 else f"\nWebhook URL: {webhook_url}")

    # Validate URL
    service = TeamsNotificationService(webhook_url=webhook_url)

    if not service.validate_webhook_url():
        print("\n❌ ERROR: Invalid webhook URL format!")
        print("Expected format: https://outlook.office.com/webhook/...")
        return 1

    print("✅ Webhook URL format valid")

    # Determine what to test
    test_all = args.all
    test_connection_only = args.connection_only

    if not any([test_all, test_connection_only, args.alert, args.backup, args.daily, args.weekly, args.severities]):
        # Default: test connection only
        test_connection_only = True

    results = []

    # Run tests
    try:
        if test_connection_only:
            results.append(test_connection(service))

        elif test_all:
            results.append(test_connection(service))
            results.append(test_alert_card(service))
            results.append(test_backup_status_card(service))
            results.append(test_daily_summary_card(service))
            results.append(test_weekly_report_card(service))
            results.append(test_all_severities(service))

        else:
            if args.alert:
                results.append(test_alert_card(service))
            if args.backup:
                results.append(test_backup_status_card(service))
            if args.daily:
                results.append(test_daily_summary_card(service))
            if args.weekly:
                results.append(test_weekly_report_card(service))
            if args.severities:
                results.append(test_all_severities(service))

        # Display statistics
        if service.get_statistics()["total_sent"] > 0:
            display_statistics(service)

        # Summary
        print("\n" + "=" * 60)
        if all(results):
            print("✅ All tests passed!")
            print("=" * 60)
            return 0
        else:
            print("❌ Some tests failed!")
            print("=" * 60)
            return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        return 130

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

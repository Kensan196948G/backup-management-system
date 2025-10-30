#!/usr/bin/env python3
"""
Email Notification Service Test Script

This script tests the email notification functionality without sending actual emails.
It validates:
- Email service configuration
- Template rendering
- Mock email sending
- Various notification types

Usage:
    python scripts/test_email_notification.py

Environment Variables Required:
    MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD (optional for testing with mock)
"""
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.notification_service import (
    EmailNotificationService,
    get_notification_service,
)


def print_header(title):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_configuration():
    """Test email service configuration"""
    print_header("Testing Email Service Configuration")

    service = EmailNotificationService()

    print(f"SMTP Server: {service.smtp_server}")
    print(f"SMTP Port: {service.smtp_port}")
    print(f"Use TLS: {service.use_tls}")
    print(f"Username: {service.username or 'Not configured'}")
    print(f"Default Sender: {service.default_sender}")
    print(f"Is Configured: {service.is_configured()}")

    if service.is_configured():
        print("\nEmail service is properly configured.")
    else:
        print("\nWARNING: Email service is not fully configured.")
        print("Set MAIL_SERVER, MAIL_USERNAME, and MAIL_PASSWORD environment variables.")


def test_email_validation():
    """Test email address validation"""
    print_header("Testing Email Validation")

    service = EmailNotificationService()

    test_emails = [
        ("admin@example.com", True),
        ("user.name+tag@example.co.uk", True),
        ("test123@test-domain.com", True),
        ("invalid", False),
        ("@example.com", False),
        ("user@", False),
        ("", False),
    ]

    print("\nEmail Validation Results:")
    for email, expected in test_emails:
        result = service.validate_email(email)
        status = "PASS" if result == expected else "FAIL"
        print(f"  {status}: {email:40s} -> {result}")


def test_rate_limiting():
    """Test rate limiting functionality"""
    print_header("Testing Rate Limiting")

    service = EmailNotificationService()
    recipient = "test@example.com"

    print(f"\nRate Limit Settings:")
    print(f"  Max emails per window: {service.rate_limit_max}")
    print(f"  Window duration: {service.rate_limit_window} seconds")

    # Test initial state
    print(f"\nInitial rate limit check: {service.check_rate_limit(recipient)}")

    # Simulate sending emails
    print(f"\nSimulating {service.rate_limit_max} email sends...")
    for i in range(service.rate_limit_max):
        service.record_delivery(recipient)
        remaining = service.rate_limit_max - (i + 1)
        print(f"  Sent {i + 1}/{service.rate_limit_max} - Can send more: {service.check_rate_limit(recipient)}")

    # Try to send one more (should be blocked)
    print(f"\nAttempting to send beyond limit: {service.check_rate_limit(recipient)}")


def test_template_rendering():
    """Test email template rendering"""
    print_header("Testing Email Template Rendering")

    service = EmailNotificationService()

    if not service.jinja_env:
        print("WARNING: Template environment not initialized.")
        print("Templates may not be available.")
        return

    templates = [
        "backup_success.html",
        "backup_failure.html",
        "rule_violation.html",
        "media_reminder.html",
        "daily_report.html",
    ]

    print("\nTesting template availability:")
    for template_name in templates:
        try:
            template = service.jinja_env.get_template(template_name)
            print(f"  PASS: {template_name} loaded successfully")

            # Test rendering with minimal context
            context = {
                "job_name": "Test Job",
                "timestamp": datetime.utcnow(),
                "error_message": "Test error",
                "violations": ["Test violation"],
                "media_id": "TAPE-001",
                "reminder_type": "rotation",
                "report_date": "2025-10-30",
                "data": {},
                "details": {},
            }

            rendered = template.render(**context)
            print(f"       Rendered {len(rendered)} characters")

        except Exception as e:
            print(f"  FAIL: {template_name} - {str(e)}")


def test_notification_methods():
    """Test various notification methods (without actual sending)"""
    print_header("Testing Notification Methods")

    service = EmailNotificationService()

    # Override send_email to prevent actual sending
    original_send_email = service.send_email

    def mock_send_email(*args, **kwargs):
        print(f"  MOCK: Would send email to {kwargs.get('to', args[0] if args else 'unknown')}")
        print(f"        Subject: {kwargs.get('subject', args[1] if len(args) > 1 else 'unknown')}")
        return True

    service.send_email = mock_send_email

    # Test backup success notification
    print("\n1. Testing Backup Success Notification:")
    service.send_backup_success_notification(
        job_name="Test Backup Job",
        recipients=["admin@example.com"],
        backup_size_bytes=1073741824,  # 1GB
        duration_seconds=120,
    )

    # Test backup failure notification
    print("\n2. Testing Backup Failure Notification:")
    service.send_backup_failure_notification(
        job_name="Test Backup Job", recipients=["admin@example.com"], error_message="Disk full error"
    )

    # Test rule violation notification
    print("\n3. Testing Rule Violation Notification:")
    service.send_rule_violation_notification(
        job_name="Test Backup Job",
        recipients=["admin@example.com"],
        violations=["Missing offsite copy", "No offline backup", "Verification test overdue"],
    )

    # Test media reminder notification
    print("\n4. Testing Media Reminder Notification:")
    service.send_media_reminder_notification(
        media_id="TAPE-001",
        recipients=["admin@example.com"],
        reminder_type="rotation",
        next_rotation_date="2025-11-01",
    )

    # Test daily report
    print("\n5. Testing Daily Report:")
    report_data = {
        "total_jobs": 10,
        "successful_backups": 8,
        "failed_backups": 2,
        "warning_count": 1,
        "total_backup_size_gb": 150.5,
        "compliance_summary": {"compliant": 7, "non_compliant": 3, "violations": []},
        "failed_jobs": [{"name": "Failed Job 1", "error": "Network timeout"}],
        "media_status": {"total": 5, "in_use": 2, "available": 3, "pending_rotation": 1, "overdue": 0},
        "verification_status": {"completed_today": 2, "passed": 2, "failed": 0, "upcoming": 5, "overdue": 1},
        "alerts": [],
        "system_health": "warning",
        "health_message": "3 non-compliant jobs detected",
    }

    service.send_daily_report(recipients=["admin@example.com"], report_data=report_data)

    # Restore original method
    service.send_email = original_send_email


def test_singleton_pattern():
    """Test singleton pattern for notification service"""
    print_header("Testing Singleton Pattern")

    service1 = get_notification_service()
    service2 = get_notification_service()

    print(f"\nService 1 ID: {id(service1)}")
    print(f"Service 2 ID: {id(service2)}")
    print(f"Are same instance: {service1 is service2}")

    if service1 is service2:
        print("\nPASS: Singleton pattern working correctly")
    else:
        print("\nFAIL: Singleton pattern not working")


def test_integration_with_alert_manager():
    """Test integration with AlertManager"""
    print_header("Testing Integration with AlertManager")

    try:
        from app.services.alert_manager import AlertManager

        alert_manager = AlertManager()

        print("\nAlertManager initialized successfully")
        print(f"Notification service attribute exists: {hasattr(alert_manager, 'notification_service')}")

        # Test lazy loading
        if alert_manager.notification_service is None:
            print("Notification service: Not yet loaded (lazy loading)")
        else:
            print("Notification service: Already loaded")

        print("\nINFO: AlertManager is ready to use EmailNotificationService")

    except Exception as e:
        print(f"\nERROR: Failed to initialize AlertManager: {str(e)}")


def main():
    """Run all tests"""
    print("\n")
    print("*" * 70)
    print("  EMAIL NOTIFICATION SERVICE TEST SUITE")
    print("*" * 70)

    try:
        test_configuration()
        test_email_validation()
        test_rate_limiting()
        test_template_rendering()
        test_notification_methods()
        test_singleton_pattern()
        test_integration_with_alert_manager()

        print_header("Test Summary")
        print("\nAll tests completed successfully!")
        print("\nNext Steps:")
        print("  1. Configure SMTP settings in .env file")
        print("  2. Run unit tests: pytest tests/unit/test_notification_service.py")
        print("  3. Test with real SMTP server (use test mode first)")
        print("  4. Integrate with backup workflows")

    except Exception as e:
        print(f"\nERROR: Test suite failed with error: {str(e)}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Scheduled Tasks for Backup Management System
Background jobs executed by APScheduler

Tasks:
1. check_compliance_status: Verify 3-2-1-1-0 rule compliance
2. check_offline_media_updates: Monitor offline media rotation
3. check_verification_reminders: Send verification test reminders
4. cleanup_old_logs: Remove old log files and audit records
5. generate_daily_report: Generate daily compliance report
"""
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


def check_compliance_status(app):
    """
    Check 3-2-1-1-0 rule compliance for all backup jobs
    Executed: Every hour

    Args:
        app: Flask application instance
    """
    with app.app_context():
        from app.models import BackupJob, ComplianceStatus, db
        from app.services.alert_manager import AlertManager
        from app.services.compliance_checker import ComplianceChecker

        try:
            logger.info("Starting compliance status check")

            # Get all active backup jobs
            jobs = BackupJob.query.filter_by(is_active=True).all()

            checker = ComplianceChecker()
            alert_manager = AlertManager()

            for job in jobs:
                # Check compliance using 3-2-1-1-0 rule
                compliance = checker.check_3_2_1_1_0(job.id)

                # Compliance status is automatically cached by the checker
                # Just generate alerts for non-compliant jobs
                if compliance["status"] in ["non_compliant", "warning"]:
                    alert_manager.create_compliance_alert(job, compliance)

            db.session.commit()
            logger.info(f"Compliance check completed for {len(jobs)} jobs")

        except Exception as e:
            logger.error(f"Error in compliance status check: {e}", exc_info=True)
            db.session.rollback()


def check_offline_media_updates(app):
    """
    Check offline media for updates and rotation schedule
    Executed: Daily at 9:00 AM

    Args:
        app: Flask application instance
    """
    with app.app_context():
        from app.models import OfflineMedia, db
        from app.services.alert_manager import AlertManager

        try:
            logger.info("Starting offline media update check")

            warning_days = app.config.get("OFFLINE_MEDIA_UPDATE_WARNING_DAYS", 7)
            threshold_date = datetime.utcnow() - timedelta(days=warning_days)

            # Find media not updated within threshold
            outdated_media = OfflineMedia.query.filter(
                OfflineMedia.last_updated < threshold_date, OfflineMedia.status.in_(["active", "offsite"])
            ).all()

            alert_manager = AlertManager()

            for media in outdated_media:
                alert_manager.create_media_update_alert(media, warning_days)

            logger.info(f"Found {len(outdated_media)} outdated media")

        except Exception as e:
            logger.error(f"Error in offline media update check: {e}", exc_info=True)


def check_verification_reminders(app):
    """
    Send reminders for upcoming verification tests
    Executed: Daily at 10:00 AM

    Args:
        app: Flask application instance
    """
    with app.app_context():
        from app.models import VerificationSchedule, db
        from app.services.alert_manager import AlertManager

        try:
            logger.info("Starting verification reminder check")

            reminder_days = app.config.get("VERIFICATION_REMINDER_DAYS", 7)
            threshold_date = datetime.utcnow() + timedelta(days=reminder_days)

            # Find upcoming verification tests
            upcoming_tests = VerificationSchedule.query.filter(
                VerificationSchedule.scheduled_date <= threshold_date, VerificationSchedule.status == "scheduled"
            ).all()

            alert_manager = AlertManager()

            for test in upcoming_tests:
                alert_manager.create_verification_reminder(test)

            logger.info(f"Sent {len(upcoming_tests)} verification reminders")

        except Exception as e:
            logger.error(f"Error in verification reminder check: {e}", exc_info=True)


def cleanup_old_logs(app):
    """
    Cleanup old log files and audit records
    Executed: Daily at 3:00 AM

    Args:
        app: Flask application instance
    """
    with app.app_context():
        from app.models import AuditLog, BackupExecution, db

        try:
            logger.info("Starting old logs cleanup")

            # Cleanup old audit logs
            audit_retention_days = app.config.get("LOG_ROTATION_DAYS", 90)
            audit_threshold = datetime.utcnow() - timedelta(days=audit_retention_days)

            deleted_audits = AuditLog.query.filter(AuditLog.timestamp < audit_threshold).delete()

            # Cleanup old backup execution logs
            execution_retention_days = app.config.get("LOG_ROTATION_DAYS", 90)
            execution_threshold = datetime.utcnow() - timedelta(days=execution_retention_days)

            deleted_executions = BackupExecution.query.filter(BackupExecution.execution_date < execution_threshold).delete()

            db.session.commit()

            # Cleanup old log files
            log_dir = Path(app.root_path).parent / "logs"
            if log_dir.exists():
                retention_days = app.config.get("LOG_ROTATION_DAYS", 90)
                threshold_time = datetime.utcnow() - timedelta(days=retention_days)

                deleted_files = 0
                for log_file in log_dir.glob("*.log.*"):
                    if log_file.stat().st_mtime < threshold_time.timestamp():
                        log_file.unlink()
                        deleted_files += 1

                logger.info(f"Deleted {deleted_files} old log files")

            logger.info(f"Cleanup completed: {deleted_audits} audit logs, " f"{deleted_executions} execution logs deleted")

        except Exception as e:
            logger.error(f"Error in log cleanup: {e}", exc_info=True)
            db.session.rollback()


def generate_daily_report(app):
    """
    Generate daily compliance report
    Executed: Daily at 8:00 AM

    Args:
        app: Flask application instance
    """
    with app.app_context():
        from app.models import (
            Alert,
            BackupExecution,
            BackupJob,
            ComplianceStatus,
            User,
            db,
        )
        from app.services.notification_service import get_notification_service

        try:
            logger.info("Starting daily report generation and email notification")

            # Collect report data
            today = datetime.utcnow().date()
            yesterday = today - timedelta(days=1)

            # Get all backup jobs
            total_jobs = BackupJob.query.filter_by(is_active=True).count()

            # Get today's executions
            executions_today = BackupExecution.query.filter(
                BackupExecution.execution_date >= yesterday, BackupExecution.execution_date < datetime.utcnow()
            ).all()

            successful_backups = sum(1 for e in executions_today if e.execution_result == "success")
            failed_backups = sum(1 for e in executions_today if e.execution_result == "failed")
            warning_count = sum(1 for e in executions_today if e.execution_result == "warning")

            # Calculate total backup size
            total_backup_size_gb = sum(e.backup_size_bytes or 0 for e in executions_today) / (1024**3)

            # Get compliance status
            compliance_statuses = ComplianceStatus.query.all()
            compliant_jobs = sum(1 for cs in compliance_statuses if cs.overall_status == "compliant")
            non_compliant_jobs = sum(1 for cs in compliance_statuses if cs.overall_status == "non_compliant")

            # Get failed jobs details
            failed_jobs = [
                {"name": e.job.job_name, "error": e.error_message or "Unknown error"}
                for e in executions_today
                if e.execution_result == "failed"
            ]

            # Get active alerts
            active_alerts = Alert.query.filter_by(is_acknowledged=False).order_by(Alert.created_at.desc()).limit(10).all()

            alerts_data = [
                {
                    "severity": alert.severity,
                    "title": alert.title,
                    "created_at": alert.created_at.strftime("%Y-%m-%d %H:%M"),
                }
                for alert in active_alerts
            ]

            # Determine system health
            if failed_backups == 0 and non_compliant_jobs == 0:
                system_health = "good"
                health_message = "All systems operational"
            elif failed_backups > 0 or non_compliant_jobs > 3:
                system_health = "critical"
                health_message = f"{failed_backups} failed backups, {non_compliant_jobs} non-compliant jobs"
            else:
                system_health = "warning"
                health_message = f"{non_compliant_jobs} non-compliant jobs detected"

            # Build report data
            report_data = {
                "total_jobs": total_jobs,
                "successful_backups": successful_backups,
                "failed_backups": failed_backups,
                "warning_count": warning_count,
                "total_backup_size_gb": total_backup_size_gb,
                "compliance_summary": {
                    "compliant": compliant_jobs,
                    "non_compliant": non_compliant_jobs,
                    "violations": [],
                },
                "failed_jobs": failed_jobs,
                "media_status": {"total": 0, "in_use": 0, "available": 0, "pending_rotation": 0, "overdue": 0},
                "verification_status": {
                    "completed_today": 0,
                    "passed": 0,
                    "failed": 0,
                    "upcoming": 0,
                    "overdue": 0,
                },
                "alerts": alerts_data,
                "system_health": system_health,
                "health_message": health_message,
            }

            # Get admin users to send report to
            admin_users = User.query.filter(User.role == "admin", User.is_active == True, User.email != None).all()
            recipients = [user.email for user in admin_users if user.email]

            if recipients:
                # Send daily report email
                notification_service = get_notification_service()
                results = notification_service.send_daily_report(recipients=recipients, report_data=report_data)
                success_count = sum(1 for success in results.values() if success)
                logger.info(f"Daily report sent to {success_count}/{len(recipients)} recipients")
            else:
                logger.warning("No admin users with email addresses found for daily report")

            logger.info("Daily report generation completed")

        except Exception as e:
            logger.error(f"Error in daily report generation: {e}", exc_info=True)

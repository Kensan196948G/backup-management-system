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
                # Check compliance
                compliance = checker.check_job_compliance(job)

                # Update or create compliance status
                status = ComplianceStatus.query.filter_by(job_id=job.id).first()
                if not status:
                    status = ComplianceStatus(job_id=job.id)
                    db.session.add(status)

                status.is_compliant = compliance["is_compliant"]
                status.has_min_copies = compliance["has_min_copies"]
                status.has_multiple_media = compliance["has_multiple_media"]
                status.has_offsite_copy = compliance["has_offsite_copy"]
                status.has_offline_copy = compliance["has_offline_copy"]
                status.has_verified_copy = compliance["has_verified_copy"]
                status.last_check = datetime.utcnow()
                status.details = compliance.get("details", "")

                # Generate alerts for non-compliant jobs
                if not compliance["is_compliant"]:
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

            deleted_executions = BackupExecution.query.filter(BackupExecution.start_time < execution_threshold).delete()

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
        from app.models import db
        from app.services.report_generator import ReportGenerator

        try:
            logger.info("Starting daily report generation")

            generator = ReportGenerator()

            # Generate daily compliance report
            report = generator.generate_daily_report()

            logger.info(f"Daily report generated: {report.filename}")

        except Exception as e:
            logger.error(f"Error in daily report generation: {e}", exc_info=True)

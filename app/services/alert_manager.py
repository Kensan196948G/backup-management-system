"""
Alert Manager Service

Manages alert generation, notification delivery, and acknowledgment.
Supports multiple notification channels:
- Database alerts
- Email notifications
- Microsoft Teams webhooks
"""
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from app.config import Config
from app.models import Alert, BackupJob, User, db

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertType(Enum):
    """Alert type enumeration"""

    BACKUP_FAILED = "backup_failed"
    BACKUP_SUCCESS = "backup_success"
    RULE_VIOLATION = "rule_violation"
    COMPLIANCE_WARNING = "compliance_warning"
    OFFLINE_MEDIA_UPDATE_WARNING = "offline_media_update_warning"
    VERIFICATION_REMINDER = "verification_reminder"
    MEDIA_ROTATION_REMINDER = "media_rotation_reminder"
    MEDIA_OVERDUE_RETURN = "media_overdue_return"
    SYSTEM_ERROR = "system_error"


class AlertManager:
    """
    Manages alert generation and notification delivery.

    Responsibilities:
    - Create alerts for various events
    - Send notifications via multiple channels
    - Track alert acknowledgment
    - Query and filter alerts
    """

    def __init__(self):
        """Initialize alert manager"""
        self.mail_service = None  # Lazy load when needed

    def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        job_id: Optional[int] = None,
        notify: bool = True,
    ) -> Alert:
        """
        Create a new alert and optionally send notifications.

        Args:
            alert_type: Type of alert (AlertType enum)
            severity: Severity level (AlertSeverity enum)
            title: Short title
            message: Detailed message
            job_id: Related backup job ID (optional)
            notify: Whether to send notifications

        Returns:
            Created Alert object
        """
        try:
            # Create alert record
            alert = Alert(
                alert_type=alert_type.value if isinstance(alert_type, AlertType) else alert_type,
                severity=severity.value if isinstance(severity, AlertSeverity) else severity,
                title=title,
                message=message,
                job_id=job_id,
                is_acknowledged=False,
            )

            db.session.add(alert)
            db.session.commit()

            logger.info(f"Alert created: {alert_type} - {title}")

            # Send notifications if requested
            if notify:
                self.send_notifications(alert)

            return alert

        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}", exc_info=True)
            db.session.rollback()
            raise

    def send_notifications(self, alert: Alert) -> Dict[str, bool]:
        """
        Send alert notifications via configured channels.

        Args:
            alert: Alert object to notify about

        Returns:
            Dictionary indicating success of each channel
        """
        results = {"email": False, "teams": False, "dashboard": True}  # Always succeeds as it's just DB storage

        try:
            # Always logged to dashboard/database
            logger.info(f"Alert notification sent to dashboard: {alert.title}")

            # Send email notifications
            if self._should_send_email(alert):
                results["email"] = self._send_email_notification(alert)

            # Send Microsoft Teams notification
            if self._should_send_teams(alert):
                results["teams"] = self._send_teams_notification(alert)

            return results

        except Exception as e:
            logger.error(f"Error sending notifications for alert {alert.id}: {str(e)}")
            return results

    def _should_send_email(self, alert: Alert) -> bool:
        """
        Determine if email notification should be sent.

        Returns:
            True if email should be sent
        """
        if not Config.MAIL_SERVER or not Config.MAIL_USERNAME:
            return False

        # Send emails for warning and error severity
        return alert.severity in ["warning", "error", "critical"]

    def _send_email_notification(self, alert: Alert) -> bool:
        """
        Send email notification.

        Args:
            alert: Alert to send

        Returns:
            True if successful
        """
        try:
            # Lazy load email service
            if self.mail_service is None:
                from app.utils.email import EmailService

                self.mail_service = EmailService()

            # Get email recipients
            recipients = self._get_email_recipients(alert)

            if not recipients:
                logger.warning(f"No email recipients found for alert {alert.id}")
                return False

            # Build email content
            subject = f"[{alert.severity.upper()}] {alert.title}"
            body = self._build_email_body(alert)

            # Send emails
            for recipient in recipients:
                try:
                    self.mail_service.send(to=recipient, subject=subject, html=body)
                except Exception as e:
                    logger.error(f"Failed to send email to {recipient}: {str(e)}")

            logger.info(f"Email notification sent for alert {alert.id}")
            return True

        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False

    def _should_send_teams(self, alert: Alert) -> bool:
        """
        Determine if Microsoft Teams notification should be sent.

        Returns:
            True if Teams should be notified
        """
        if not Config.TEAMS_WEBHOOK_URL:
            return False

        # Send Teams notifications for error and critical severity
        return alert.severity in ["error", "critical"]

    def _send_teams_notification(self, alert: Alert) -> bool:
        """
        Send Microsoft Teams notification via webhook.

        Args:
            alert: Alert to send

        Returns:
            True if successful
        """
        try:
            import requests

            # Build Adaptive Card
            card = self._build_adaptive_card(alert)

            payload = {
                "type": "message",
                "attachments": [{"contentType": "application/vnd.microsoft.card.adaptive", "content": card}],
            }

            # Send to Teams webhook
            response = requests.post(Config.TEAMS_WEBHOOK_URL, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info(f"Teams notification sent for alert {alert.id}")
                return True
            else:
                logger.error(f"Teams webhook returned status {response.status_code}: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending Teams notification: {str(e)}")
            return False

    def _get_email_recipients(self, alert: Alert) -> List[str]:
        """
        Get email recipients for an alert.

        Args:
            alert: Alert to send

        Returns:
            List of email addresses
        """
        try:
            recipients = []

            # Add job owner if alert is job-related
            if alert.job_id:
                job = BackupJob.query.get(alert.job_id)
                if job and job.owner and job.owner.email:
                    recipients.append(job.owner.email)

            # Add admin users
            admin_users = User.query.filter(User.role == "admin", User.is_active == True, User.email != None).all()

            for user in admin_users:
                if user.email not in recipients:
                    recipients.append(user.email)

            return recipients

        except Exception as e:
            logger.error(f"Error getting email recipients: {str(e)}")
            return []

    def _build_email_body(self, alert: Alert) -> str:
        """
        Build HTML email body.

        Args:
            alert: Alert to format

        Returns:
            HTML email body
        """
        color_map = {"info": "#17a2b8", "warning": "#ffc107", "error": "#dc3545", "critical": "#721c24"}

        color = color_map.get(alert.severity, "#6c757d")

        job_info = ""
        if alert.job_id:
            job = BackupJob.query.get(alert.job_id)
            if job:
                job_info = f"<p><strong>Job:</strong> {job.job_name}</p>"

        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="background-color: white; padding: 20px; border-radius: 5px;
                            border-left: 5px solid {color};">
                    <h2 style="color: {color}; margin-top: 0;">
                        [{alert.severity.upper()}] {alert.title}
                    </h2>
                    {job_info}
                    <p>{alert.message}</p>
                    <hr style="border-color: #e0e0e0;">
                    <p style="color: #666; font-size: 12px;">
                        Alert ID: {alert.id}<br>
                        Created: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
                    </p>
                </div>
            </body>
        </html>
        """

        return html

    def _build_adaptive_card(self, alert: Alert) -> Dict:
        """
        Build Microsoft Teams Adaptive Card.

        Args:
            alert: Alert to format

        Returns:
            Adaptive Card JSON dictionary
        """
        color_map = {"info": "#0078D4", "warning": "#FFB900", "error": "#E81123", "critical": "#C50F1F"}

        color = color_map.get(alert.severity, "#737373")

        facts = [
            {"title": "Type", "value": alert.alert_type},
            {"title": "Severity", "value": alert.severity.upper()},
            {"title": "Created", "value": alert.created_at.strftime("%Y-%m-%d %H:%M:%S")},
        ]

        if alert.job_id:
            job = BackupJob.query.get(alert.job_id)
            if job:
                facts.insert(1, {"title": "Job", "value": job.job_name})

        card = {
            "type": "AdaptiveCard",
            "version": "1.2",
            "body": [
                {"type": "TextBlock", "text": alert.title, "weight": "Bolder", "size": "Large", "color": color},
                {"type": "TextBlock", "text": alert.message, "wrap": True, "spacing": "Medium"},
                {"type": "FactSet", "facts": facts, "spacing": "Medium"},
            ],
        }

        return card

    def acknowledge_alert(self, alert_id: int, user_id: int) -> Alert:
        """
        Mark alert as acknowledged.

        Args:
            alert_id: Alert ID
            user_id: User acknowledging the alert

        Returns:
            Updated Alert object
        """
        try:
            alert = Alert.query.get(alert_id)
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")

            alert.is_acknowledged = True
            alert.acknowledged_by = user_id
            alert.acknowledged_at = datetime.utcnow()

            db.session.commit()

            logger.info(f"Alert {alert_id} acknowledged by user {user_id}")

            return alert

        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {str(e)}")
            db.session.rollback()
            raise

    def get_unacknowledged_alerts(self, limit: int = 50) -> List[Alert]:
        """
        Get unacknowledged alerts.

        Args:
            limit: Maximum number of alerts to return

        Returns:
            List of Alert objects
        """
        try:
            alerts = Alert.query.filter_by(is_acknowledged=False).order_by(Alert.created_at.desc()).limit(limit).all()

            return alerts

        except Exception as e:
            logger.error(f"Error fetching unacknowledged alerts: {str(e)}")
            return []

    def get_alerts_by_job(self, job_id: int, days: int = 30, limit: int = 100) -> List[Alert]:
        """
        Get alerts for a specific job.

        Args:
            job_id: Backup job ID
            days: Look back this many days
            limit: Maximum number of alerts to return

        Returns:
            List of Alert objects
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            alerts = (
                Alert.query.filter(Alert.job_id == job_id, Alert.created_at >= since_date)
                .order_by(Alert.created_at.desc())
                .limit(limit)
                .all()
            )

            return alerts

        except Exception as e:
            logger.error(f"Error fetching alerts for job {job_id}: {str(e)}")
            return []

    def get_alerts_by_type(self, alert_type: str, days: int = 30, limit: int = 100) -> List[Alert]:
        """
        Get alerts of a specific type.

        Args:
            alert_type: Alert type to filter by
            days: Look back this many days
            limit: Maximum number of alerts to return

        Returns:
            List of Alert objects
        """
        try:
            since_date = datetime.utcnow() - timedelta(days=days)

            alerts = (
                Alert.query.filter(Alert.alert_type == alert_type, Alert.created_at >= since_date)
                .order_by(Alert.created_at.desc())
                .limit(limit)
                .all()
            )

            return alerts

        except Exception as e:
            logger.error(f"Error fetching alerts of type {alert_type}: {str(e)}")
            return []

    def clear_old_alerts(self, days: int = 90) -> int:
        """
        Delete acknowledged alerts older than specified days.

        Args:
            days: Delete alerts older than this many days

        Returns:
            Number of deleted alerts
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            count = Alert.query.filter(Alert.is_acknowledged == True, Alert.acknowledged_at < cutoff_date).delete()

            db.session.commit()

            logger.info(f"Cleared {count} old acknowledged alerts")

            return count

        except Exception as e:
            logger.error(f"Error clearing old alerts: {str(e)}")
            db.session.rollback()
            return 0

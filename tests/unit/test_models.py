"""
Unit tests for database models.

Tests all 14 models with focus on:
- CRUD operations
- Relationships
- Model methods
- Field validations
- Default values
"""
from datetime import datetime, timedelta

import pytest
from werkzeug.security import check_password_hash

from app.models import (
    Alert,
    AuditLog,
    BackupCopy,
    BackupExecution,
    BackupJob,
    ComplianceStatus,
    MediaLending,
    MediaRotationSchedule,
    OfflineMedia,
    Report,
    SystemSetting,
    User,
    VerificationSchedule,
    VerificationTest,
    db,
)


class TestUserModel:
    """Test cases for User model."""

    def test_create_user(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com", role="operator")
            user.set_password("password123")
            db.session.add(user)
            db.session.commit()

            assert user.id is not None
            assert user.username == "testuser"
            assert user.email == "test@example.com"
            assert user.role == "operator"
            assert user.is_active is True
            assert user.created_at is not None
            assert user.updated_at is not None

    def test_password_hashing(self, app):
        """Test password hashing and verification."""
        with app.app_context():
            user = User(username="testuser", email="test@example.com")
            user.set_password("mypassword")

            assert user.password_hash is not None
            assert user.password_hash != "mypassword"
            assert user.check_password("mypassword") is True
            assert user.check_password("wrongpassword") is False

    def test_user_roles(self, app, admin_user, operator_user, auditor_user):
        """Test user role checking methods."""
        with app.app_context():
            # Refresh objects from database
            admin = db.session.get(User, admin_user.id)
            operator = db.session.get(User, operator_user.id)
            auditor = db.session.get(User, auditor_user.id)

            # Test admin
            assert admin.is_admin() is True
            assert admin.is_operator() is False
            assert admin.is_auditor() is False
            assert admin.can_edit() is True
            assert admin.can_view() is True

            # Test operator
            assert operator.is_admin() is False
            assert operator.is_operator() is True
            assert operator.is_auditor() is False
            assert operator.can_edit() is True
            assert operator.can_view() is True

            # Test auditor
            assert auditor.is_admin() is False
            assert auditor.is_operator() is False
            assert auditor.is_auditor() is True
            assert auditor.can_edit() is False
            assert auditor.can_view() is True

    def test_user_repr(self, app, admin_user):
        """Test user string representation."""
        with app.app_context():
            user = db.session.get(User, admin_user.id)
            assert repr(user) == f"<User {user.username}>"

    def test_inactive_user(self, app):
        """Test inactive user creation."""
        with app.app_context():
            user = User(username="inactive", email="inactive@example.com", role="operator", is_active=False)
            db.session.add(user)
            db.session.commit()

            assert user.is_active is False


class TestBackupJobModel:
    """Test cases for BackupJob model."""

    def test_create_backup_job(self, app):
        """Test creating a backup job."""
        with app.app_context():
            job = BackupJob(
                name="Test Job",
                description="Test Description",
                source_path="/data/test",
                schedule_type="daily",
                schedule_time="02:00",
                retention_days=30,
            )
            db.session.add(job)
            db.session.commit()

            assert job.id is not None
            assert job.name == "Test Job"
            assert job.source_path == "/data/test"
            assert job.schedule_type == "daily"
            assert job.is_active is True

    def test_backup_job_relationships(self, app, backup_job, backup_copies):
        """Test BackupJob relationships."""
        with app.app_context():
            job = db.session.get(BackupJob, backup_job.id)

            assert len(job.copies) == 4
            assert all(copy.job_id == job.id for copy in job.copies)

    def test_backup_job_default_values(self, app):
        """Test BackupJob default values."""
        with app.app_context():
            job = BackupJob(name="Minimal Job", source_path="/data/minimal")
            db.session.add(job)
            db.session.commit()

            assert job.is_active is True
            assert job.created_at is not None
            assert job.updated_at is not None

    def test_backup_job_repr(self, app, backup_job):
        """Test BackupJob string representation."""
        with app.app_context():
            job = db.session.get(BackupJob, backup_job.id)
            assert repr(job) == f"<BackupJob {job.name}>"


class TestBackupCopyModel:
    """Test cases for BackupCopy model."""

    def test_create_backup_copy(self, app, backup_job):
        """Test creating a backup copy."""
        with app.app_context():
            copy = BackupCopy(
                job_id=backup_job.id,
                copy_number=1,
                storage_location="Test Storage",
                media_type="disk",
                is_offsite=False,
                is_offline=False,
                is_encrypted=True,
                is_compressed=True,
                size_bytes=1024,
                checksum="abc123",
                status="success",
            )
            db.session.add(copy)
            db.session.commit()

            assert copy.id is not None
            assert copy.job_id == backup_job.id
            assert copy.copy_number == 1
            assert copy.is_encrypted is True

    def test_backup_copy_3_2_1_1_0_fields(self, app, backup_copies):
        """Test 3-2-1-1-0 rule specific fields."""
        with app.app_context():
            copies = [db.session.get(BackupCopy, c.id) for c in backup_copies]

            # Check media types (requirement: 2 different types)
            media_types = set(c.media_type for c in copies)
            assert len(media_types) >= 2

            # Check offsite copy (requirement: 1 offsite)
            offsite_copies = [c for c in copies if c.is_offsite]
            assert len(offsite_copies) >= 1

            # Check offline copy (requirement: 1 offline)
            offline_copies = [c for c in copies if c.is_offline]
            assert len(offline_copies) >= 1

    def test_backup_copy_relationship(self, app, backup_job, backup_copies):
        """Test BackupCopy relationship with BackupJob."""
        with app.app_context():
            copy = db.session.get(BackupCopy, backup_copies[0].id)
            assert copy.job is not None
            assert copy.job.id == backup_job.id

    def test_backup_copy_repr(self, app, backup_copies):
        """Test BackupCopy string representation."""
        with app.app_context():
            copy = db.session.get(BackupCopy, backup_copies[0].id)
            expected = f"<BackupCopy Job:{copy.job_id} Copy:{copy.copy_number}>"
            assert repr(copy) == expected


class TestOfflineMediaModel:
    """Test cases for OfflineMedia model."""

    def test_create_offline_media(self, app):
        """Test creating offline media."""
        with app.app_context():
            media = OfflineMedia(
                media_type="tape",
                media_label="TAPE-001",
                barcode="BC001",
                capacity_bytes=2000000000000,
                location="Vault A",
                current_status="available",
            )
            db.session.add(media)
            db.session.commit()

            assert media.id is not None
            assert media.media_type == "tape"
            assert media.current_status == "available"

    def test_offline_media_capacity_tracking(self, app, offline_media):
        """Test media capacity and usage tracking."""
        with app.app_context():
            media = db.session.get(OfflineMedia, offline_media[0].id)

            assert media.capacity_bytes > 0
            assert media.used_bytes is not None
            assert media.used_bytes <= media.capacity_bytes

    def test_offline_media_repr(self, app, offline_media):
        """Test OfflineMedia string representation."""
        with app.app_context():
            media = db.session.get(OfflineMedia, offline_media[0].id)
            assert repr(media) == f"<OfflineMedia {media.media_label}>"


class TestMediaRotationScheduleModel:
    """Test cases for MediaRotationSchedule model."""

    def test_create_rotation_schedule(self, app, offline_media):
        """Test creating a media rotation schedule."""
        with app.app_context():
            schedule = MediaRotationSchedule(
                media_id=offline_media[0].id, rotation_type="weekly", rotation_day="Monday", notes="Weekly rotation schedule"
            )
            db.session.add(schedule)
            db.session.commit()

            assert schedule.id is not None
            assert schedule.rotation_type == "weekly"
            assert schedule.is_active is True

    def test_rotation_schedule_relationship(self, app, offline_media):
        """Test MediaRotationSchedule relationship with OfflineMedia."""
        with app.app_context():
            schedule = MediaRotationSchedule(media_id=offline_media[0].id, rotation_type="daily")
            db.session.add(schedule)
            db.session.commit()

            assert schedule.media is not None
            assert schedule.media.id == offline_media[0].id


class TestMediaLendingModel:
    """Test cases for MediaLending model."""

    def test_create_media_lending(self, app, offline_media):
        """Test creating a media lending record."""
        with app.app_context():
            lending = MediaLending(
                media_id=offline_media[0].id,
                lent_to="John Doe",
                lent_date=datetime.utcnow(),
                purpose="Backup verification",
                expected_return_date=datetime.utcnow() + timedelta(days=7),
            )
            db.session.add(lending)
            db.session.commit()

            assert lending.id is not None
            assert lending.lent_to == "John Doe"
            assert lending.return_date is None

    def test_media_lending_return(self, app, offline_media):
        """Test returning lent media."""
        with app.app_context():
            lending = MediaLending(
                media_id=offline_media[0].id, lent_to="Jane Doe", lent_date=datetime.utcnow(), purpose="Testing"
            )
            db.session.add(lending)
            db.session.commit()

            # Return the media
            lending.return_date = datetime.utcnow()
            db.session.commit()

            assert lending.return_date is not None


class TestVerificationTestModel:
    """Test cases for VerificationTest model."""

    def test_create_verification_test(self, app, backup_copies):
        """Test creating a verification test."""
        with app.app_context():
            test = VerificationTest(
                copy_id=backup_copies[0].id,
                test_type="checksum",
                status="success",
                result_message="Checksum verified successfully",
            )
            db.session.add(test)
            db.session.commit()

            assert test.id is not None
            assert test.test_type == "checksum"
            assert test.status == "success"

    def test_verification_test_with_error(self, app, backup_copies):
        """Test verification test with error details."""
        with app.app_context():
            test = VerificationTest(
                copy_id=backup_copies[0].id,
                test_type="restore",
                status="failed",
                result_message="Restore failed",
                error_details="Checksum mismatch detected",
            )
            db.session.add(test)
            db.session.commit()

            assert test.status == "failed"
            assert test.error_details is not None


class TestVerificationScheduleModel:
    """Test cases for VerificationSchedule model."""

    def test_create_verification_schedule(self, app, backup_job):
        """Test creating a verification schedule."""
        with app.app_context():
            schedule = VerificationSchedule(
                job_id=backup_job.id, test_type="checksum", frequency_days=7, next_run=datetime.utcnow() + timedelta(days=7)
            )
            db.session.add(schedule)
            db.session.commit()

            assert schedule.id is not None
            assert schedule.frequency_days == 7
            assert schedule.is_active is True


class TestBackupExecutionModel:
    """Test cases for BackupExecution model."""

    def test_create_backup_execution(self, app, backup_job):
        """Test creating a backup execution record."""
        with app.app_context():
            execution = BackupExecution(
                job_id=backup_job.id,
                status="success",
                start_time=datetime.utcnow() - timedelta(hours=1),
                end_time=datetime.utcnow(),
                total_size=1024000,
                total_files=100,
            )
            db.session.add(execution)
            db.session.commit()

            assert execution.id is not None
            assert execution.status == "success"
            assert execution.total_files == 100

    def test_backup_execution_with_error(self, app, backup_job):
        """Test backup execution with error."""
        with app.app_context():
            execution = BackupExecution(
                job_id=backup_job.id, status="failed", start_time=datetime.utcnow(), error_message="Disk full"
            )
            db.session.add(execution)
            db.session.commit()

            assert execution.status == "failed"
            assert execution.error_message is not None


class TestComplianceStatusModel:
    """Test cases for ComplianceStatus model."""

    def test_create_compliance_status(self, app, backup_job):
        """Test creating a compliance status record."""
        with app.app_context():
            status = ComplianceStatus(
                job_id=backup_job.id,
                is_compliant=True,
                total_copies=4,
                media_types_count=3,
                has_offsite=True,
                has_offline=True,
                details={"rule": "3-2-1-1-0", "status": "compliant"},
            )
            db.session.add(status)
            db.session.commit()

            assert status.id is not None
            assert status.is_compliant is True
            assert status.total_copies == 4

    def test_non_compliant_status(self, app, backup_job):
        """Test non-compliant status."""
        with app.app_context():
            status = ComplianceStatus(
                job_id=backup_job.id,
                is_compliant=False,
                total_copies=2,
                media_types_count=1,
                has_offsite=False,
                has_offline=False,
                details={"missing": "offsite and offline copies"},
            )
            db.session.add(status)
            db.session.commit()

            assert status.is_compliant is False
            assert status.has_offsite is False


class TestAlertModel:
    """Test cases for Alert model."""

    def test_create_alert(self, app, backup_job):
        """Test creating an alert."""
        with app.app_context():
            alert = Alert(
                job_id=backup_job.id,
                alert_type="compliance",
                severity="high",
                message="Backup compliance violation",
                details={"issue": "Missing offsite copy"},
            )
            db.session.add(alert)
            db.session.commit()

            assert alert.id is not None
            assert alert.alert_type == "compliance"
            assert alert.is_acknowledged is False

    def test_acknowledge_alert(self, app, backup_job):
        """Test acknowledging an alert."""
        with app.app_context():
            alert = Alert(job_id=backup_job.id, alert_type="warning", severity="medium", message="Low disk space")
            db.session.add(alert)
            db.session.commit()

            # Acknowledge the alert
            alert.is_acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = 1
            db.session.commit()

            assert alert.is_acknowledged is True
            assert alert.acknowledged_at is not None


class TestAuditLogModel:
    """Test cases for AuditLog model."""

    def test_create_audit_log(self, app, admin_user):
        """Test creating an audit log entry."""
        with app.app_context():
            log = AuditLog(
                user_id=admin_user.id,
                action="create_backup_job",
                resource_type="BackupJob",
                resource_id=1,
                details={"job_name": "Test Job"},
                ip_address="192.168.1.1",
            )
            db.session.add(log)
            db.session.commit()

            assert log.id is not None
            assert log.action == "create_backup_job"
            assert log.user_id == admin_user.id

    def test_audit_log_without_user(self, app):
        """Test audit log for system actions."""
        with app.app_context():
            log = AuditLog(action="system_backup", resource_type="System", details={"automated": True})
            db.session.add(log)
            db.session.commit()

            assert log.user_id is None


class TestReportModel:
    """Test cases for Report model."""

    def test_create_report(self, app):
        """Test creating a report."""
        with app.app_context():
            report = Report(
                report_type="daily",
                title="Daily Backup Report",
                period_start=datetime.utcnow() - timedelta(days=1),
                period_end=datetime.utcnow(),
                data={"total_jobs": 10, "successful": 9, "failed": 1},
                file_path="/reports/daily_2025.pdf",
                generated_by="system",
            )
            db.session.add(report)
            db.session.commit()

            assert report.id is not None
            assert report.report_type == "daily"
            assert report.data is not None

    def test_report_repr(self, app):
        """Test Report string representation."""
        with app.app_context():
            report = Report(
                report_type="weekly", title="Weekly Report", period_start=datetime.utcnow(), period_end=datetime.utcnow()
            )
            db.session.add(report)
            db.session.commit()

            assert repr(report) == f"<Report {report.report_type}>"


class TestSystemSettingModel:
    """Test cases for SystemSetting model."""

    def test_create_system_setting(self, app):
        """Test creating a system setting."""
        with app.app_context():
            setting = SystemSetting(
                category="backup", key="min_copies", value="3", description="Minimum number of backup copies"
            )
            db.session.add(setting)
            db.session.commit()

            assert setting.id is not None
            assert setting.category == "backup"
            assert setting.key == "min_copies"

    def test_encrypted_setting(self, app):
        """Test encrypted system setting."""
        with app.app_context():
            setting = SystemSetting(category="credentials", key="api_key", value="secret_key_value", is_encrypted=True)
            db.session.add(setting)
            db.session.commit()

            assert setting.is_encrypted is True

    def test_system_setting_repr(self, app):
        """Test SystemSetting string representation."""
        with app.app_context():
            setting = SystemSetting(category="test", key="test_key", value="test_value")
            db.session.add(setting)
            db.session.commit()

            expected = f"<SystemSetting {setting.category}.{setting.key}>"
            assert repr(setting) == expected

#!/usr/bin/env python3
"""
Verification Service Demonstration

This script demonstrates the backup verification and restore testing functionality.
Run this to test the verification service with sample data.

Usage:
    python examples/verification_demo.py
"""

import shutil
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import create_app
from app.models import BackupCopy, BackupJob, User, db
from app.services.verification_service import (
    TestResult,
    VerificationType,
    get_verification_service,
)


def create_test_data():
    """Create test backup job and sample files"""
    print("=" * 80)
    print("BACKUP VERIFICATION SERVICE DEMONSTRATION")
    print("=" * 80)
    print()

    # Create test user
    user = User.query.filter_by(username="admin").first()
    if not user:
        user = User(
            username="demo_admin",
            email="admin@demo.com",
            role="admin",
            full_name="Demo Administrator",
            is_active=True,
        )
        user.set_password("demo123")
        db.session.add(user)
        db.session.commit()
        print(f"✓ Created demo user: {user.username}")
    else:
        print(f"✓ Using existing user: {user.username}")

    # Create test backup job
    job = BackupJob(
        job_name="Demo Backup Job",
        job_type="file",
        backup_tool="custom",
        schedule_type="daily",
        retention_days=30,
        owner_id=user.id,
        description="Demo backup job for verification testing",
        is_active=True,
    )
    db.session.add(job)
    db.session.commit()
    print(f"✓ Created backup job: {job.job_name} (ID: {job.id})")

    # Create temporary directories
    source_dir = Path(tempfile.mkdtemp(prefix="demo_source_"))
    backup_dir = Path(tempfile.mkdtemp(prefix="demo_backup_"))

    print(f"✓ Created source directory: {source_dir}")
    print(f"✓ Created backup directory: {backup_dir}")

    # Create sample files
    file_count = 10
    for i in range(file_count):
        file_path = source_dir / f"sample_file_{i:03d}.txt"
        content = f"Sample File {i}\n" + ("=" * 50 + "\n") * 20
        file_path.write_text(content)

    print(f"✓ Created {file_count} sample files in source directory")

    # Simulate backup (copy to backup directory)
    for file in source_dir.glob("*.txt"):
        shutil.copy2(file, backup_dir / file.name)

    print(f"✓ Copied files to backup directory")

    # Create backup copy record
    backup_copy = BackupCopy(
        job_id=job.id,
        copy_type="primary",
        media_type="disk",
        storage_path=str(backup_dir),
        is_encrypted=False,
        is_compressed=False,
        status="success",
    )
    db.session.add(backup_copy)
    db.session.commit()
    print(f"✓ Created backup copy record")
    print()

    return user.id, job.id, source_dir, backup_dir


def run_integrity_check(job_id, user_id):
    """Demonstrate integrity check"""
    print("-" * 80)
    print("1. INTEGRITY CHECK TEST")
    print("-" * 80)
    print("Testing: Checksum validation without restoration")
    print()

    service = get_verification_service()

    result, details = service.execute_verification_test(job_id=job_id, test_type=VerificationType.INTEGRITY, tester_id=user_id)

    print(f"Test Result: {result.value}")
    print(f"Test Type: {details['test_type']}")
    print(f"Total Files Checked: {details['total_files_checked']}")
    print(f"Total Files Valid: {details['total_files_valid']}")
    print(f"Validity Rate: {details['validity_rate']:.2f}%")

    if details.get("errors"):
        print(f"\nErrors:")
        for error in details["errors"]:
            print(f"  - {error}")
    else:
        print("\n✓ No errors detected")

    print()
    return result


def run_partial_restore_test(job_id, user_id):
    """Demonstrate partial restore test"""
    print("-" * 80)
    print("2. PARTIAL RESTORE TEST")
    print("-" * 80)
    print("Testing: Selective file restoration and verification")
    print()

    service = get_verification_service()

    result, details = service.execute_verification_test(job_id=job_id, test_type=VerificationType.PARTIAL, tester_id=user_id)

    print(f"Test Result: {result.value}")
    print(f"Test Type: {details['test_type']}")
    print(f"Files Tested: {details['files_tested']}")
    print(f"Verified Files: {details['verified_files']}")
    print(f"Failed Files: {details['failed_files']}")
    print(f"Success Rate: {details['success_rate']:.2f}%")

    if details.get("errors"):
        print(f"\nErrors:")
        for error in details["errors"]:
            print(f"  - {error}")
    else:
        print("\n✓ No errors detected")

    print()
    return result


def run_full_restore_test(job_id, user_id):
    """Demonstrate full restore test"""
    print("-" * 80)
    print("3. FULL RESTORE TEST")
    print("-" * 80)
    print("Testing: Complete backup restoration and verification")
    print()

    service = get_verification_service()

    result, details = service.execute_verification_test(
        job_id=job_id, test_type=VerificationType.FULL_RESTORE, tester_id=user_id
    )

    print(f"Test Result: {result.value}")
    print(f"Test Type: {details['test_type']}")
    print(f"Total Files Restored: {details['total_files_restored']}")
    print(f"Total Files Verified: {details['total_files_verified']}")
    print(f"Verification Rate: {details['verification_rate']:.2f}%")

    if details.get("copies_tested"):
        print(f"\nCopies Tested:")
        for copy in details["copies_tested"]:
            print(f"  - Type: {copy['copy_type']}")
            print(f"    Files Restored: {copy['files_restored']}")
            print(f"    Files Verified: {copy['files_verified']}")

    if details.get("errors"):
        print(f"\nErrors:")
        for error in details["errors"]:
            print(f"  - {error}")
    else:
        print("\n✓ No errors detected")

    print()
    return result


def demonstrate_scheduling(job_id, user_id):
    """Demonstrate verification scheduling"""
    print("-" * 80)
    print("4. VERIFICATION SCHEDULING")
    print("-" * 80)
    print("Testing: Automated verification scheduling")
    print()

    service = get_verification_service()

    # Schedule monthly verification
    schedule = service.schedule_verification_test(job_id=job_id, test_frequency="monthly", assigned_to=user_id)

    print(f"✓ Scheduled monthly verification")
    print(f"  Job ID: {schedule.job_id}")
    print(f"  Frequency: {schedule.test_frequency}")
    print(f"  Next Test Date: {schedule.next_test_date}")
    print(f"  Assigned To: {schedule.assigned_to}")
    print(f"  Is Active: {schedule.is_active}")
    print()

    # Check for overdue tests
    overdue = service.get_overdue_verification_tests()
    print(f"✓ Checked for overdue tests: {len(overdue)} found")
    print()


def show_statistics(service):
    """Show verification statistics"""
    print("-" * 80)
    print("5. VERIFICATION STATISTICS")
    print("-" * 80)
    print()

    stats = service.get_statistics()

    print("Session Statistics:")
    print(f"  Total Tests: {stats['total_tests']}")
    print(f"  Successful Tests: {stats['successful_tests']}")
    print(f"  Failed Tests: {stats['failed_tests']}")
    print(f"  Last Test: {stats['last_test']}")
    print()

    print("Database Statistics:")
    print(f"  Total Tests: {stats['db_total_tests']}")
    print(f"  Successful Tests: {stats['db_successful_tests']}")
    print(f"  Failed Tests: {stats['db_failed_tests']}")
    print(f"  Success Rate: {stats['db_success_rate']:.2f}%")
    print()


def cleanup(job_id, source_dir, backup_dir):
    """Cleanup test data"""
    print("-" * 80)
    print("CLEANUP")
    print("-" * 80)
    print()

    # Remove database records
    BackupCopy.query.filter_by(job_id=job_id).delete()
    BackupJob.query.filter_by(id=job_id).delete()
    db.session.commit()
    print("✓ Removed database records")

    # Remove temporary directories
    shutil.rmtree(source_dir, ignore_errors=True)
    shutil.rmtree(backup_dir, ignore_errors=True)
    print(f"✓ Removed temporary directories")
    print()


def main():
    """Main demonstration function"""
    app = create_app()

    with app.app_context():
        # Create test data
        user_id, job_id, source_dir, backup_dir = create_test_data()

        try:
            # Run demonstrations
            integrity_result = run_integrity_check(job_id, user_id)
            partial_result = run_partial_restore_test(job_id, user_id)
            full_result = run_full_restore_test(job_id, user_id)

            # Demonstrate scheduling
            demonstrate_scheduling(job_id, user_id)

            # Show statistics
            service = get_verification_service()
            show_statistics(service)

            # Summary
            print("=" * 80)
            print("DEMONSTRATION SUMMARY")
            print("=" * 80)
            print()
            print(f"Integrity Check: {integrity_result.value}")
            print(f"Partial Restore: {partial_result.value}")
            print(f"Full Restore: {full_result.value}")
            print()

            all_passed = all(
                r in [TestResult.SUCCESS, TestResult.WARNING] for r in [integrity_result, partial_result, full_result]
            )

            if all_passed:
                print("✓ All verification tests completed successfully!")
            else:
                print("⚠ Some verification tests failed. Please review the output.")

            print()

        finally:
            # Cleanup
            cleanup(job_id, source_dir, backup_dir)

        print("=" * 80)
        print("DEMONSTRATION COMPLETE")
        print("=" * 80)


if __name__ == "__main__":
    main()

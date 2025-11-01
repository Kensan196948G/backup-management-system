"""
Pydantic schemas for API request/response validation
Provides type-safe data validation for REST API endpoints
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# ============================================================================
# Base Response Models
# ============================================================================


class APIResponse(BaseModel):
    """Base API response model"""

    success: bool = Field(default=True, description="Request success status")
    message: Optional[str] = Field(default=None, description="Response message")
    data: Optional[Any] = Field(default=None, description="Response data")

    model_config = ConfigDict(from_attributes=True)


class ErrorResponse(BaseModel):
    """Error response model"""

    success: bool = Field(default=False, description="Request success status")
    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")

    model_config = ConfigDict(from_attributes=True)


class PaginatedResponse(BaseModel):
    """Paginated response model"""

    success: bool = Field(default=True, description="Request success status")
    data: List[Any] = Field(default_factory=list, description="Response data items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Backup Models
# ============================================================================


class BackupJobCreate(BaseModel):
    """Request model for creating a backup job"""

    name: str = Field(..., min_length=1, max_length=200, description="Backup job name")
    description: Optional[str] = Field(default=None, max_length=500, description="Job description")
    source_path: str = Field(..., min_length=1, description="Source directory path")
    backup_type: str = Field(..., description="Backup type: full, incremental, differential")
    schedule_type: str = Field(..., description="Schedule type: daily, weekly, monthly, custom")
    schedule_time: Optional[str] = Field(default=None, description="Schedule time in HH:MM format")
    schedule_days: Optional[str] = Field(default=None, description="Schedule days (comma-separated)")
    retention_days: int = Field(default=30, ge=1, le=3650, description="Retention period in days")
    is_active: bool = Field(default=True, description="Active status")
    priority: int = Field(default=5, ge=1, le=10, description="Priority level (1-10)")
    notification_email: Optional[str] = Field(default=None, description="Notification email address")
    tags: Optional[str] = Field(default=None, description="Tags (comma-separated)")

    @field_validator("backup_type")
    @classmethod
    def validate_backup_type(cls, v):
        allowed = ["full", "incremental", "differential"]
        if v not in allowed:
            raise ValueError(f'backup_type must be one of: {", ".join(allowed)}')
        return v

    @field_validator("schedule_type")
    @classmethod
    def validate_schedule_type(cls, v):
        allowed = ["daily", "weekly", "monthly", "custom"]
        if v not in allowed:
            raise ValueError(f'schedule_type must be one of: {", ".join(allowed)}')
        return v

    model_config = ConfigDict(from_attributes=True)


class BackupJobUpdate(BaseModel):
    """Request model for updating a backup job"""

    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=500)
    source_path: Optional[str] = Field(default=None, min_length=1)
    backup_type: Optional[str] = Field(default=None)
    schedule_type: Optional[str] = Field(default=None)
    schedule_time: Optional[str] = Field(default=None)
    schedule_days: Optional[str] = Field(default=None)
    retention_days: Optional[int] = Field(default=None, ge=1, le=3650)
    is_active: Optional[bool] = Field(default=None)
    priority: Optional[int] = Field(default=None, ge=1, le=10)
    notification_email: Optional[str] = Field(default=None)
    tags: Optional[str] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class BackupJobResponse(BaseModel):
    """Response model for backup job details"""

    id: int
    name: str
    description: Optional[str]
    source_path: str
    backup_type: str
    schedule_type: str
    schedule_time: Optional[str]
    schedule_days: Optional[str]
    retention_days: int
    is_active: bool
    priority: int
    notification_email: Optional[str]
    tags: Optional[str]
    owner_id: int
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    last_result: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class BackupExecutionResponse(BaseModel):
    """Response model for backup execution details"""

    id: int
    job_id: int
    execution_date: datetime
    execution_result: str
    error_message: Optional[str]
    backup_size_bytes: Optional[int]
    duration_seconds: Optional[int]
    source_system: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class BackupTrigger(BaseModel):
    """Request model for triggering a manual backup"""

    backup_type: Optional[str] = Field(default="full", description="Backup type override")
    notify: bool = Field(default=True, description="Send notification on completion")

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Storage Models
# ============================================================================


class StorageProviderResponse(BaseModel):
    """Response model for storage provider details"""

    id: int
    name: str
    provider_type: str
    location_type: str
    connection_string: Optional[str]
    capacity_bytes: Optional[int]
    used_bytes: Optional[int]
    is_online: bool
    is_active: bool
    created_at: datetime
    last_verified: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class StorageTestRequest(BaseModel):
    """Request model for testing storage connection"""

    provider_type: str = Field(..., description="Provider type: local, network, cloud, tape")
    connection_string: str = Field(..., min_length=1, description="Connection string or path")
    credentials: Optional[Dict[str, str]] = Field(default=None, description="Authentication credentials")

    @field_validator("provider_type")
    @classmethod
    def validate_provider_type(cls, v):
        allowed = ["local", "network", "cloud", "tape", "s3", "azure", "gcs"]
        if v not in allowed:
            raise ValueError(f'provider_type must be one of: {", ".join(allowed)}')
        return v

    model_config = ConfigDict(from_attributes=True)


class StorageTestResponse(BaseModel):
    """Response model for storage connection test result"""

    success: bool
    provider_type: str
    connection_string: str
    accessible: bool
    writable: bool
    total_space_bytes: Optional[int]
    free_space_bytes: Optional[int]
    latency_ms: Optional[float]
    error_message: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class StorageSpaceResponse(BaseModel):
    """Response model for storage space information"""

    id: int
    name: str
    provider_type: str
    total_bytes: Optional[int]
    used_bytes: Optional[int]
    free_bytes: Optional[int]
    utilization_percent: Optional[float]
    backup_count: int
    last_updated: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Verification Models
# ============================================================================


class VerificationStartRequest(BaseModel):
    """Request model for starting verification"""

    test_type: str = Field(..., description="Test type: checksum, restore, read")
    scope: str = Field(default="full", description="Verification scope: full, sample, quick")
    notify_on_completion: bool = Field(default=True, description="Send notification on completion")

    @field_validator("test_type")
    @classmethod
    def validate_test_type(cls, v):
        allowed = ["checksum", "restore", "read", "integrity"]
        if v not in allowed:
            raise ValueError(f'test_type must be one of: {", ".join(allowed)}')
        return v

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, v):
        allowed = ["full", "sample", "quick"]
        if v not in allowed:
            raise ValueError(f'scope must be one of: {", ".join(allowed)}')
        return v

    model_config = ConfigDict(from_attributes=True)


class VerificationStatusResponse(BaseModel):
    """Response model for verification status"""

    id: int
    backup_id: int
    test_type: str
    test_status: str
    test_result: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    files_tested: Optional[int]
    files_passed: Optional[int]
    files_failed: Optional[int]
    error_message: Optional[str]
    tester_id: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class VerificationResultResponse(BaseModel):
    """Response model for verification result summary"""

    backup_id: int
    backup_name: str
    test_type: str
    test_status: str
    test_result: Optional[str]
    success_rate: Optional[float]
    total_files: Optional[int]
    passed_files: Optional[int]
    failed_files: Optional[int]
    duration_seconds: Optional[int]
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Compliance Models
# ============================================================================


class ComplianceStatusResponse(BaseModel):
    """Response model for compliance status"""

    job_id: int
    job_name: str
    rule_3_copies: bool
    rule_2_media: bool
    rule_1_offsite: bool
    rule_1_offline: bool
    rule_0_errors: bool
    overall_compliant: bool
    primary_count: int
    secondary_count: int
    offsite_count: int
    offline_count: int
    verification_passed: bool
    last_checked: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# Authentication Models
# ============================================================================


class TokenRequest(BaseModel):
    """Request model for token authentication"""

    username: str = Field(..., min_length=1, description="Username")
    password: str = Field(..., min_length=1, description="Password")

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Response model for token"""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int

    model_config = ConfigDict(from_attributes=True)


class APIKeyCreate(BaseModel):
    """Request model for creating API key"""

    name: str = Field(..., min_length=1, max_length=100, description="API key name")
    description: Optional[str] = Field(default=None, max_length=500, description="Key description")
    expires_at: Optional[datetime] = Field(default=None, description="Expiration datetime")
    scopes: Optional[List[str]] = Field(default=None, description="API scopes/permissions")

    model_config = ConfigDict(from_attributes=True)


class APIKeyResponse(BaseModel):
    """Response model for API key"""

    id: int
    name: str
    description: Optional[str]
    key: str  # Only returned on creation
    created_at: datetime
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

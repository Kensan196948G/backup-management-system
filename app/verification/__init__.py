"""
Verification and Validation Module

This module provides comprehensive file integrity verification and validation
services for the backup management system.

Features:
- Multiple checksum algorithms (SHA-256, SHA-512, BLAKE2)
- Streaming checksum calculation for large files
- Parallel processing for multiple files
- File integrity validation
- Metadata verification
- Bit rot detection
"""

from .checksum import ChecksumService
from .interfaces import IVerificationService
from .validator import FileValidator

__all__ = [
    "IVerificationService",
    "ChecksumService",
    "FileValidator",
]

__version__ = "1.0.0"

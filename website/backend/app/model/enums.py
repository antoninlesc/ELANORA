"""Shared enums for the application.

This module contains all enum definitions used across models.
"""

from enum import Enum


class UserRole(str, Enum):
    """Enum for user roles."""

    ADMIN = "admin"
    PUBLIC = "public"


class ProjectPermission(str, Enum):
    """Enumeration for project permissions."""

    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"

    @classmethod
    def _missing_(cls, value):
        if isinstance(value, str):
            for member in cls:
                if member.value == value.lower():
                    return member
        return None


class InvitationStatus(str, Enum):
    """Enumeration for invitation status."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class Type(str, Enum):
    """Enumeration for conflict types."""

    # Original ELAN conflict types
    ANNOTATION_OVERLAP = "annotation_overlap"
    TIER_MISMATCH = "tier_mismatch"
    VALUE_DIFFERENCE = "value_difference"
    STRUCTURAL = "structural"
    OTHER = "other"

    # Upload workflow types
    PENDING_UPLOAD = "pending_upload"
    UPLOAD_NEW_FILES_ONLY = "upload_new_files_only"
    UPLOAD_WITH_MODIFICATIONS = "upload_with_modifications"
    UPLOAD_WITH_DELETIONS = "upload_with_deletions"
    UPLOAD_MIXED_CHANGES = "upload_mixed_changes"


class Severity(str, Enum):
    """Enumeration for conflict severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Status(str, Enum):
    """Enumeration for conflict status."""

    PENDING_ADMIN_APPROVAL = "pending_admin_approval"
    READY_TO_MERGE = "ready_to_merge"
    NEEDS_RESOLUTION = "needs_resolution"
    BEING_REVIEWED = "being_reviewed"
    # Final statuses
    RESOLVED = "resolved"  # Successfully merged
    DISMISSED = "dismissed"  # Rejected/cancelled


class CommentTargetType(str, Enum):
    """Enumeration for comment target types."""

    PROJECT = "project"
    ELAN_FILE = "elan_file"
    CONFLICT = "conflict"
    TIER = "tier"
    ANNOTATION = "annotation"

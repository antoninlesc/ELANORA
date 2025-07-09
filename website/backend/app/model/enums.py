"""
Shared enums for the application.

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


class InvitationStatus(str, Enum):
    """Enumeration for invitation status."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ConflictType(str, Enum):
    """Enumeration for conflict types."""

    ANNOTATION_OVERLAP = "annotation_overlap"
    TIER_MISMATCH = "tier_mismatch"
    VALUE_DIFFERENCE = "value_difference"
    STRUCTURAL = "structural"
    OTHER = "other"


class ConflictSeverity(str, Enum):
    """Enumeration for conflict severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConflictStatus(str, Enum):
    """Enumeration for conflict status."""

    DETECTED = "detected"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class CommentTargetType(str, Enum):
    """Enumeration for comment target types."""

    PROJECT = "project"
    ELAN_FILE = "elan_file"
    CONFLICT = "conflict"
    TIER = "tier"
    ANNOTATION = "annotation"

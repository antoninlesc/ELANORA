"""
SQLAlchemy models package.

This module imports all models in the correct order to avoid circular imports.
Models are imported based on their dependencies, with base models first.
"""

# Import enums first
from .enums import (
    UserRole,
    ProjectPermission,
    InvitationStatus,
    ConflictType,
    ConflictSeverity,
    ConflictStatus,
    CommentTargetType,
)

# Base models with no dependencies
from .annotation_standard import AnnotationStandard
from .country import Country
from .instance import Instance

# Models with single dependencies
from .city import City
from .address import Address

# User model (depends on address)
from .user import User

# Project model (depends on instance)
from .project import Project

# Models with dependencies on user/project
from .elan_file import ElanFile
from .invitation import Invitation
from .conflict import Conflict
from .comment import Comment

# Tier and annotation models
from .tier import Tier
from .annotation import Annotation

# Association tables (import last)
from .associations import (
    ElanFileToProject,
    ElanFileToTier,
    ProjectAnnotStandard,
    UserToProject,
    UserWorkOnConflict,
    ConflictOfElanFile,
    CommentProject,
    CommentElanFile,
    CommentConflict,
)

__all__ = [
    # Enums
    "UserRole",
    "ProjectPermission",
    "InvitationStatus",
    "ConflictType",
    "ConflictSeverity",
    "ConflictStatus",
    "CommentTargetType",
    # Base models
    "AnnotationStandard",
    "Country",
    "Instance",
    # Location models
    "City",
    "Address",
    # User model
    "User",
    # Project model
    "Project",
    # File and content models
    "ElanFile",
    "Tier",
    "Annotation",
    # Collaboration models
    "Invitation",
    "Conflict",
    "Comment",
    # Association tables
    "ElanFileToProject",
    "ElanFileToTier",
    "ProjectAnnotStandard",
    "UserToProject",
    "UserWorkOnConflict",
    "ConflictOfElanFile",
    "CommentProject",
    "CommentElanFile",
    "CommentConflict",
]

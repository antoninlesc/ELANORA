"""SQLAlchemy models package.

This module imports all models in the correct order to avoid circular imports.
Models are imported based on their dependencies, with base models first.
"""

# Import enums first
from .address import Address
from .annotation import Annotation

# Base models with no dependencies
from .annotation_standard import AnnotationStandard

# Association tables (import last)
from .association import (
    CommentConflict,
    CommentElanFile,
    CommentProject,
    ConflictOfElanFile,
    ElanFileToProject,
    ElanFileToTier,
    ProjectAnnotStandard,
    UserToProject,
    UserWorkOnConflict,
)

# Models with single dependencies
from .city import City
from .comment import Comment
from .conflict import Conflict
from .country import Country

# Models with dependencies on user/project
from .elan_file import ElanFile
from .enums import (
    CommentTargetType,
    ConflictSeverity,
    ConflictStatus,
    ConflictType,
    InvitationStatus,
    ProjectPermission,
    UserRole,
)
from .instance import Instance
from .invitation import Invitation

# Project model (depends on instance)
from .project import Project

# Tier and annotation models
from .tier import Tier

# User model (depends on address)
from .user import User

__all__ = [
    "Address",
    "Annotation",
    "AnnotationStandard",
    "City",
    "Comment",
    "CommentConflict",
    "CommentElanFile",
    "CommentProject",
    "CommentTargetType",
    "Conflict",
    "ConflictOfElanFile",
    "ConflictSeverity",
    "ConflictStatus",
    "ConflictType",
    "Country",
    "ElanFile",
    "ElanFileToProject",
    "ElanFileToTier",
    "Instance",
    "Invitation",
    "InvitationStatus",
    "Project",
    "ProjectAnnotStandard",
    "ProjectPermission",
    "Tier",
    "User",
    "UserRole",
    "UserToProject",
    "UserWorkOnConflict",
]

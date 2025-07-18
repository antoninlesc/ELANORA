"""SQLAlchemy models package.

This module imports all models in the correct order to avoid circular imports.
Models are imported based on their dependencies, with base models first.
"""

# Import enums first
from .address import Address
from .annotation import Annotation
from .annotation_value import AnnotationValue

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
from .elan_file_media import ElanFileMedia
from .association import ElanFileToMedia

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
from .tier_group import TierGroup
from .tier_section import TierSection

# User model (depends on address)
from .user import User

__all__ = [
    "Address",
    "Annotation",
    "AnnotationStandard",
    "AnnotationValue",
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
    "ElanFileMedia",
    "ElanFileToMedia",
    "ElanFileToProject",
    "ElanFileToTier",
    "Instance",
    "Invitation",
    "InvitationStatus",
    "Project",
    "ProjectAnnotStandard",
    "ProjectPermission",
    "Tier",
    "TierGroup",
    "TierSection",
    "User",
    "UserRole",
    "UserToProject",
    "UserWorkOnConflict",
]

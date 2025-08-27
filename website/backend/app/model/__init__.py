"""SQLAlchemy models package.

This module imports all models in the correct order to avoid circular imports.
Models are imported based on their dependencies, with base models first.
"""

# Import enums first
from .address import Address
from .annotation import Annotation

# Base models with no dependencies
from .annotation_standard import AnnotationStandard
from .annotation_value import AnnotationValue

# Association tables (import last)
from .association import (
    CommentConflict,
    CommentElanFile,
    CommentProject,
    ConflictOfElanFile,
    ElanFileToMedia,
    ElanFileToProject,
    ElanFileToTier,
    ProjectAnnotStandard,
    UserToProject,
    UserWorkOnConflict,
)

# Models with single dependencies
from .city import City
from .comment import Comment
from .pending_upload import PendingUpload
from .country import Country

# Models with dependencies on user/project
from .elan_file import ElanFile
from .elan_file_media import ElanFileMedia
from .enums import (
    CommentTargetType,
    Severity,
    Status,
    Type,
    InvitationStatus,
    ProjectPermission,
    UserRole,
)
from .file_type import FileType
from .instance import Instance
from .invitation import Invitation

# Project model (depends on instance)
from .project import Project
from .project_naming_standard import ProjectNamingStandard

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
    "PendingUpload",
    "ConflictOfElanFile",
    "Severity",
    "Status",
    "Type",
    "Country",
    "ElanFile",
    "ElanFileMedia",
    "ElanFileToMedia",
    "ElanFileToProject",
    "ElanFileToTier",
    "FileType",
    "Instance",
    "Invitation",
    "InvitationStatus",
    "NamingComponent",
    "Project",
    "ProjectAnnotStandard",
    "ProjectNamingStandard",
    "ProjectPermission",
    "Tier",
    "TierGroup",
    "TierSection",
    "User",
    "UserRole",
    "UserToProject",
    "UserWorkOnConflict",
]

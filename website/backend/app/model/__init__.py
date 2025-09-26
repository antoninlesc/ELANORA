"""SQLAlchemy models package.

This module imports all models in the correct order to avoid circular imports.
Models are imported based on their dependencies, with base models first.
"""

# Import enums first (from their respective files)
from .invitation import InvitationStatus
from .user_to_project import ProjectPermission
from .user import UserRole

# Base models with no dependencies
from .accepted_value import AcceptedValue
from .annotation_value import AnnotationValue
from .component_accepted_value import ComponentAcceptedValue
from .component_template import ComponentTemplate
from .country import Country
from .effective_naming_standard import EffectiveNamingStandard
from .file_type import FileType
from .standard_component import StandardComponent

# Models with single dependencies
from .address import Address
from .annotation import Annotation
from .city import City
from .file_content import FileContent
from .instance import Instance
from .notification import Notification
from .notification_preference import NotificationPreference
from .project_file_type import ProjectFileType
from .project_location_file_type import ProjectLocationFileType
from .project_naming_standard import ProjectNamingStandard
from .tier import Tier
from .tier_group import TierGroup
from .tier_section import TierSection
from .upload_session import UploadSession
from .user import User

# Models with multiple dependencies
from .elan_file import ElanFile
from .elan_file_media import ElanFileMedia
from .elan_file_to_media import ElanFileToMedia
from .elan_file_to_tier import ElanFileToTier
from .invitation import Invitation
from .project import Project
from .user_to_project import UserToProject

__all__ = [
    "AcceptedValue",
    "Address",
    "Annotation",
    "AnnotationValue",
    "City",
    "ComponentAcceptedValue",
    "ComponentTemplate",
    "Country",
    "EffectiveNamingStandard",
    "ElanFile",
    "ElanFileMedia",
    "ElanFileToMedia",
    "ElanFileToTier",
    "FileContent",
    "FileType",
    "Instance",
    "Invitation",
    "InvitationStatus",
    "Notification",
    "NotificationPreference",
    "Project",
    "ProjectFileType",
    "ProjectLocationFileType",
    "ProjectNamingStandard",
    "ProjectPermission",
    "StandardComponent",
    "Tier",
    "TierGroup",
    "TierSection",
    "UploadSession",
    "User",
    "UserRole",
    "UserToProject",
]

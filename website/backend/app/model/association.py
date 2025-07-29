from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.schema import UniqueConstraint

from app.db.database import Base

from .enums import ProjectPermission

ELAN_FILE_ELANID_FK = "ELAN_FILE.elan_id"
PROJECT_PROJECTID_FK = "PROJECT.project_id"
CONFLICT_CONFLICTID_FK = "CONFLICT.conflict_id"
COMMENT_COMMENTID_FK = "COMMENT.comment_id"


class ElanFileToProject(Base):
    """Association table linking ELAN files to projects."""

    __tablename__ = "ELAN_FILE_TO_PROJECT"

    elan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(ELAN_FILE_ELANID_FK), primary_key=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(PROJECT_PROJECTID_FK), primary_key=True
    )


class ElanFileToTier(Base):
    """Association table linking ELAN files to tiers."""

    __tablename__ = "ELAN_FILE_TO_TIER"

    elan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(ELAN_FILE_ELANID_FK), primary_key=True
    )
    tier_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("TIER.tier_id"), primary_key=True
    )


class ProjectAnnotStandard(Base):
    """Association table linking projects to annotation standards."""

    __tablename__ = "PROJECT_ANNOT_STANDARD"

    standard_id: Mapped[str] = mapped_column(
        String(50), ForeignKey("ANNOTATION_STANDARD.standard_id"), primary_key=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(PROJECT_PROJECTID_FK), primary_key=True
    )


class UserToProject(Base):
    """Association table linking users to projects with permissions."""

    __tablename__ = "USER_TO_PROJECT"

    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(PROJECT_PROJECTID_FK), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("USER.user_id"), primary_key=True
    )
    permission: Mapped[ProjectPermission] = mapped_column(
        String(20), nullable=False, default=ProjectPermission.READ
    )


class UserWorkOnConflict(Base):
    """Association table linking users to conflicts they work on."""

    __tablename__ = "USER_WORK_ON_CONFLICT"

    conflict_id: Mapped[str] = mapped_column(
        String(50), ForeignKey(CONFLICT_CONFLICTID_FK), primary_key=True
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("USER.user_id"), primary_key=True
    )


class ConflictOfElanFile(Base):
    """Association table linking conflicts to ELAN files."""

    __tablename__ = "CONFLICT_OF_ELAN_FILE"

    conflict_id: Mapped[str] = mapped_column(
        String(50), ForeignKey(CONFLICT_CONFLICTID_FK), primary_key=True
    )
    elan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(ELAN_FILE_ELANID_FK), primary_key=True
    )


class CommentProject(Base):
    """Association table linking comments to projects."""

    __tablename__ = "COMMENT_PROJECT"

    comment_id: Mapped[str] = mapped_column(
        String(50), ForeignKey(COMMENT_COMMENTID_FK), primary_key=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(PROJECT_PROJECTID_FK), nullable=False
    )


class CommentElanFile(Base):
    """Association table linking comments to ELAN files."""

    __tablename__ = "COMMENT_ELAN_FILE"

    comment_id: Mapped[str] = mapped_column(
        String(50), ForeignKey(COMMENT_COMMENTID_FK), primary_key=True
    )
    elan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(ELAN_FILE_ELANID_FK), nullable=False
    )


class CommentConflict(Base):
    """Association table linking comments to conflicts."""

    __tablename__ = "COMMENT_CONFLICT"

    comment_id: Mapped[str] = mapped_column(
        String(50), ForeignKey(COMMENT_COMMENTID_FK), primary_key=True
    )
    conflict_id: Mapped[str] = mapped_column(
        String(50), ForeignKey(CONFLICT_CONFLICTID_FK), nullable=False
    )


class ElanFileToMedia(Base):
    """Association table linking ELAN files to media."""

    __tablename__ = "ELAN_FILE_TO_MEDIA"

    elan_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("ELAN_FILE.elan_id", ondelete="CASCADE"), primary_key=True
    )
    media_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ELAN_FILE_MEDIA.media_id", ondelete="CASCADE"),
        primary_key=True,
    )

    # Relationships
    elan_file = relationship("ElanFile", back_populates="media_links")
    media = relationship("ElanFileMedia", back_populates="elan_files")


class ProjectFileType(Base):
    """Association table linking projects to file types with a project-specific name."""

    __tablename__ = "PROJECT_FILE_TYPE"
    __table_args__ = (
        UniqueConstraint("project_id", "name", name="uq_project_filetype_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("PROJECT.project_id"), nullable=False
    )
    file_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("FILE_TYPE.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    file_type = relationship("FileType")

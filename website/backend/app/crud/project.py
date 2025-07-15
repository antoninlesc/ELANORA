from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.model.annotation import Annotation
from app.crud.annotation import delete_unused_annotation_values
from app.model.tier import Tier
from app.model.elan_file import ElanFile
from app.model.associations import (
    ElanFileToProject,
    ElanFileToTier,
    CommentElanFile,
    ConflictOfElanFile,
    ProjectAnnotStandard,
    UserToProject,
    CommentProject,
    CommentConflict,
)
from app.model.conflict import Conflict
from app.model.invitation import Invitation
from app.model.project import Project
from app.model.enums import ProjectPermission
from app.core.centralized_logging import get_logger

logger = get_logger()

from app.model.project import Project


async def create_project_db(
    db: AsyncSession,
    project_name: str,
    description: str,
    project_path: str,
    instance_id: int,
    creator_user_id: int,
) -> Project:
    project = Project(
        project_name=project_name,
        description=description,
        project_path=project_path,
        instance_id=instance_id,
    )
    db.add(project)
    await db.flush()

    user_to_project = UserToProject(
        project_id=project.project_id,
        user_id=creator_user_id,
        permission=ProjectPermission.OWNER,
    )
    db.add(user_to_project)
    await db.commit()
    return project


async def get_project_by_name(db: AsyncSession, project_name: str) -> Project | None:
    result = await db.execute(
        select(Project).where(Project.project_name == project_name)
    )
    return result.scalars().first()


async def get_project_by_id(db: AsyncSession, project_id: int) -> Project | None:
    result = await db.execute(select(Project).where(Project.project_id == project_id))
    return result.scalars().first()


async def delete_project(db: AsyncSession, project_id: int) -> None:
    project = await get_project_by_id(db, project_id)
    if project:
        await db.delete(project)
        await db.commit()


async def list_projects_by_instance(
    db: AsyncSession, instance_id: int
) -> list[Project]:
    result = await db.execute(select(Project).where(Project.instance_id == instance_id))
    return list(result.scalars().all())


# --- ELAN FILE DELETION ---


async def delete_annotations_for_tier(db: AsyncSession, tier_id: str):
    logger.info(f"Attempting to delete annotations for tier_id={tier_id}")
    try:
        await db.execute(
            Annotation.__table__.delete().where(Annotation.tier_id == tier_id)
        )
        await db.commit()
        logger.info(f"Deleted annotations for tier_id={tier_id}")
    except Exception as e:
        logger.error(f"Failed to delete annotations for tier_id={tier_id}: {e}")


async def delete_tiers_for_elan_file(db: AsyncSession, elan_id: int):
    logger.info(f"Attempting to delete tiers for elan_id={elan_id}")
    try:
        result = await db.execute(select(Tier).where(Tier.elan_id == elan_id))
        tiers = result.scalars().all()
        for tier in tiers:
            await delete_annotations_for_tier(db, tier.tier_id)
            await db.delete(tier)
        await db.commit()
        logger.info(f"Deleted {len(tiers)} tiers for elan_id={elan_id}")
    except Exception as e:
        logger.error(f"Failed to delete tiers for elan_id={elan_id}: {e}")


async def delete_elan_file_associations(db: AsyncSession, elan_id: int):
    logger.info(f"Attempting to delete ELAN file associations for elan_id={elan_id}")
    try:
        await db.execute(
            ElanFileToTier.__table__.delete().where(ElanFileToTier.elan_id == elan_id)
        )
        await db.execute(
            CommentElanFile.__table__.delete().where(CommentElanFile.elan_id == elan_id)
        )
        await db.execute(
            ConflictOfElanFile.__table__.delete().where(
                ConflictOfElanFile.elan_id == elan_id
            )
        )
        await db.commit()
        logger.info(
            f"Deleted ELAN_FILE_TO_TIER, COMMENT_ELAN_FILE, and CONFLICT_OF_ELAN_FILE associations for elan_id={elan_id}"
        )
    except Exception as e:
        logger.error(
            f"Failed to delete ELAN file associations for elan_id={elan_id}: {e}"
        )


async def delete_elan_file(db: AsyncSession, elan_file: ElanFile):
    logger.info(
        f"Deleting ELAN file and all related data for elan_id={elan_file.elan_id}"
    )
    try:
        await delete_elan_file_associations(db, elan_file.elan_id)
        await delete_tiers_for_elan_file(db, elan_file.elan_id)
        await db.delete(elan_file)
        await db.commit()
        logger.info(f"Deleted ELAN file elan_id={elan_file.elan_id}")
    except Exception as e:
        logger.error(f"Failed to delete ELAN file elan_id={elan_file.elan_id}: {e}")


# --- PROJECT-LEVEL ASSOCIATIONS ---


async def delete_project_invitations(db: AsyncSession, project_id: int):
    logger.info(f"Deleting invitations for project_id={project_id}")
    await db.execute(
        Invitation.__table__.delete().where(Invitation.project_id == project_id)
    )


async def delete_project_conflicts(db: AsyncSession, project_id: int):
    logger.info(f"Deleting conflicts for project_id={project_id}")
    await db.execute(
        Conflict.__table__.delete().where(Conflict.project_id == project_id)
    )


async def delete_project_comments(db: AsyncSession, project_id: int):
    logger.info(f"Deleting project comments for project_id={project_id}")
    await db.execute(
        CommentProject.__table__.delete().where(CommentProject.project_id == project_id)
    )
    # Optionally, delete orphaned comments


async def delete_project_associations(db: AsyncSession, project_id: int):
    logger.info(f"Deleting project associations for project_id={project_id}")
    await db.execute(
        ElanFileToProject.__table__.delete().where(
            ElanFileToProject.project_id == project_id
        )
    )
    await db.execute(
        ProjectAnnotStandard.__table__.delete().where(
            ProjectAnnotStandard.project_id == project_id
        )
    )
    await db.execute(
        UserToProject.__table__.delete().where(UserToProject.project_id == project_id)
    )


# --- CONFLICTS AND COMMENTS ---


async def delete_conflict_comments(db: AsyncSession, conflict_id: str):
    await db.execute(
        CommentConflict.__table__.delete().where(
            CommentConflict.conflict_id == conflict_id
        )
    )


async def delete_conflict_of_elan_file(db: AsyncSession, elan_id: int):
    await db.execute(
        ConflictOfElanFile.__table__.delete().where(
            ConflictOfElanFile.elan_id == elan_id
        )
    )


# --- MAIN PROJECT DELETE FUNCTION ---


async def delete_project_db(db: AsyncSession, project_name: str) -> None:
    logger.info(f"Starting deletion for project '{project_name}'")
    # Find the project
    result = await db.execute(
        select(Project).where(Project.project_name == project_name)
    )
    project = result.scalars().first()
    if not project:
        logger.warning(f"Project '{project_name}' not found for deletion.")
        return

    # Find all ELAN files associated with this project BEFORE deleting associations
    result = await db.execute(
        select(ElanFile)
        .join(ElanFileToProject, ElanFile.elan_id == ElanFileToProject.elan_id)
        .where(ElanFileToProject.project_id == project.project_id)
    )
    elan_files = result.scalars().all()
    logger.info(
        f"Found {len(elan_files)} ELAN files for project_id={project.project_id}"
    )

    if not elan_files:
        logger.warning(
            f"No ELAN files found for project_id={project.project_id}. Check ElanFileToProject table for associations."
        )

    for elan_file in elan_files:
        logger.info(
            f"Deleting ELAN file with elan_id={elan_file.elan_id} for project_id={project.project_id}"
        )
        await delete_elan_file(db, elan_file)

    # Now delete all project-level associations
    await delete_project_associations(db, project.project_id)
    await delete_project_invitations(db, project.project_id)
    await delete_project_conflicts(db, project.project_id)
    await delete_project_comments(db, project.project_id)

    # Clean up unused annotation values after all annotations are deleted
    logger.info(
        f"Cleaning up unused annotation values after deleting project '{project_name}'"
    )
    await delete_unused_annotation_values(db)

    # Finally, delete the project
    logger.info(f"Deleting project '{project_name}' (project_id={project.project_id})")
    await db.delete(project)
    await db.commit()
    logger.info(f"Finished deletion for project '{project_name}'")


async def project_exists_by_name(db: AsyncSession, project_name: str) -> bool:
    result = await db.execute(
        select(Project).where(Project.project_name == project_name)
    )
    return result.scalars().first() is not None

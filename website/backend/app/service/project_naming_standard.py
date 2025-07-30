import logging

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import (
    project_naming_standard,
    component_template,
    accepted_value,
    component_accepted_value,
    standard_component,
    file_type
)
from app.model.project_file_type import ProjectFileType
from app.core.centralized_logging import get_logger

logger = get_logger(__name__)


class ProjectNamingStandardService:
    @staticmethod
    async def get_standards_for_project(db: AsyncSession, project_id: int):
        return await project_naming_standard.get_standards_by_project(db, project_id)

    @staticmethod
    async def get_standard_with_components(db: AsyncSession, standard_id: int):
        standard = await project_naming_standard.get_standard_by_id(db, standard_id)
        if not standard:
            return None
        std_components = await standard_component.get_components_by_standard(db, standard_id)
        return {
            "id": standard.id,
            "project_id": standard.project_id,
            "name": standard.name,
            "project_file_type_id": standard.project_file_type_id,
            "pattern": standard.pattern,
            "description": standard.description,
            "components": [
                {
                    "id": sc.component_template.id,
                    "name": sc.component_template.name,
                    "description": sc.component_template.description,
                    "regex": sc.component_template.regex,
                    "order": sc.order,
                    "accepted_values": [v.value for v in sc.component_template.accepted_values],
                    "project_file_type_id": standard.project_file_type_id,
                }
                for sc in sorted(std_components, key=lambda x: x.order)
            ],
        }

    @staticmethod
    async def create_standard_with_components(
        db: AsyncSession,
        project_id: int,
        name: str,
        project_file_type_id: int,
        pattern: str,
        description: str | None,
        components: list[dict],
    ):
        try:
            standard = await project_naming_standard.create_standard(
                db, project_id, name, project_file_type_id, pattern, description
            )
            # --- LOOKUP file_type_id ONCE ---
            project_file_type = await db.get(ProjectFileType, project_file_type_id)
            if not project_file_type:
                raise HTTPException(status_code=400, detail="Invalid project_file_type_id")
            file_type_id = project_file_type.file_type_id
            # --------------------------------
            for idx, comp in enumerate(components):
                # Use the correct file_type_id
                template = await component_template.get_or_create_component_template(
                    db,
                    file_type_id=file_type_id,
                    name=comp["name"],
                    regex=comp["regex"],
                    description=comp.get("description"),
                )
                await standard_component.link_standard_to_component(
                    db,
                    naming_standard_id=standard.id,
                    component_template_id=template.id,
                    order=comp.get("order", idx + 1),
                )
                for val in comp.get("accepted_values", []):
                    acc_val = await accepted_value.get_or_create_accepted_value(db, val)
                    await component_accepted_value.link_component_to_accepted_value(
                        db, template.id, acc_val.id
                    )
            await db.commit()
            # Return the created standard with components
            return await ProjectNamingStandardService.get_standard_with_components(db, standard.id)
        except IntegrityError as e:
            await db.rollback()
            msg = str(e.orig)
            logger.error(f"IntegrityError while creating standard: {msg}")
            if "uq_project_filetype_standard" in msg:
                raise HTTPException(
                    status_code=409,
                    detail="A standard for this file type already exists in this project.",
                ) from e
            elif "uq_project_naming_standard_name" in msg:
                raise HTTPException(
                    status_code=409,
                    detail="A standard with this name already exists in this project.",
                ) from e
            else:
                raise HTTPException(
                    status_code=409, detail=f"A database constraint was violated: {msg}"
                ) from e
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Unexpected error while creating standard: {e}", exc_info=True
            )
            raise

    @staticmethod
    async def _delete_standard_and_cleanup(db: AsyncSession, standard_id: int):
        logger.info(f"Deleting ProjectNamingStandard with id={standard_id}")
        await project_naming_standard.delete_standard(db, standard_id)

        logger.info("Cleaning up orphaned ComponentAcceptedValue rows for orphaned templates...")
        await component_accepted_value.delete_for_orphaned_templates(db)
        logger.info("Cleaning up orphaned ComponentTemplate rows...")
        await component_template.delete_orphaned_component_templates(db)
        logger.info("Cleaning up orphaned AcceptedValue rows...")
        await accepted_value.delete_orphaned_accepted_values(db)

    @staticmethod
    async def delete_standard(db: AsyncSession, standard_id: int):
        try:
            await ProjectNamingStandardService._delete_standard_and_cleanup(db, standard_id)
            logger.info("Cleaning up orphaned FileType rows...")
            await file_type.delete_orphaned_file_types(db)
            await db.commit()
            logger.info("Delete and cleanup committed successfully.")
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error during delete_standard: {e}", exc_info=True)
            raise

    @staticmethod
    async def delete_all_standards_by_project(db: AsyncSession, project_id: int):
        try:
            standard_ids = await project_naming_standard.get_standards_ids_by_project(db, project_id)
            for standard_id in standard_ids:
                await ProjectNamingStandardService._delete_standard_and_cleanup(db, standard_id)
            logger.info("Bulk delete and cleanup committed successfully.")
        except Exception as e:
            logger.error(f"Error during delete_all_standards_by_project: {e}", exc_info=True)
            raise

    @staticmethod
    async def get_unique_component_names_by_project(db, project_id: int):
        return await component_template.get_unique_component_names_by_project(db, project_id)

    @staticmethod
    async def get_project_naming_standards_full(db: AsyncSession, project_id: int):
        standards = await project_naming_standard.get_standards_by_project(db, project_id)
        standards_with_components = []
        for standard in standards:
            detail = await ProjectNamingStandardService.get_standard_with_components(db, standard.id)
            standards_with_components.append(detail)
        component_names = await component_template.get_unique_component_names_by_project(db, project_id)
        return {
            "component_names": component_names,
            "standards": standards_with_components,
        }

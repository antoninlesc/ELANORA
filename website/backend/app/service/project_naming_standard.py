import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.crud import project_naming_standard
from app.crud import naming_component

logger = logging.getLogger(__name__)


class ProjectNamingStandardService:
    @staticmethod
    async def get_standards_for_project(db: AsyncSession, project_id: int):
        return await project_naming_standard.get_standards_by_project(db, project_id)

    @staticmethod
    async def get_standard_with_components(db: AsyncSession, standard_id: int):
        standard = await project_naming_standard.get_standard_by_id(db, standard_id)
        if not standard:
            return None
        components = await naming_component.get_components_by_standard(db, standard_id)
        return {"standard": standard, "components": components}

    @staticmethod
    async def create_standard_with_components(
        db: AsyncSession,
        project_id: int,
        name: str,
        file_type_id: int,
        pattern: str,
        description: str | None,
        components: list[dict],
    ):
        try:
            standard = await project_naming_standard.create_standard(
                db, project_id, name, file_type_id, pattern, description
            )
            for idx, comp in enumerate(components):
                await naming_component.create_component(
                    db,
                    naming_standard_id=standard.id,
                    file_type_id=file_type_id,
                    name=comp["name"],
                    regex=comp["regex"],
                    description=comp.get("description"),
                    order=comp.get("order", idx + 1),
                    accepted_values=comp.get("accepted_values", []),
                )
            await db.commit()
            components_objs = await naming_component.get_components_by_standard(
                db, standard.id
            )
            return {
                "id": standard.id,
                "project_id": standard.project_id,
                "name": standard.name,
                "file_type_id": standard.file_type_id,
                "pattern": standard.pattern,
                "description": standard.description,
                "components": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "regex": c.regex,
                        "description": c.description,
                        "order": c.order,
                        "accepted_values": getattr(c, "accepted_values_list", []),
                        "file_type_id": c.file_type_id,
                    }
                    for c in components_objs
                ],
            }
        except IntegrityError as e:
            await db.rollback()
            msg = str(e.orig)
            logger.error(f"IntegrityError while creating standard: {msg}")
            if "uq_project_filetype_standard" in msg:
                raise HTTPException(
                    status_code=409,
                    detail="A standard for this file type already exists in this project.",
                )
            elif "uq_project_naming_standard_name" in msg:
                raise HTTPException(
                    status_code=409,
                    detail="A standard with this name already exists in this project.",
                )
            else:
                raise HTTPException(
                    status_code=409, detail=f"A database constraint was violated: {msg}"
                )
        except Exception as e:
            await db.rollback()
            logger.error(
                f"Unexpected error while creating standard: {e}", exc_info=True
            )
            raise

    @staticmethod
    async def update_standard_and_components(
        db: AsyncSession,
        standard_id: int,
        update_fields: dict,
        components: list[dict],
    ):
        try:
            await project_naming_standard.update_standard(
                db, standard_id, update_fields
            )
            # Remove old components
            await naming_component.delete_components_by_standard(db, standard_id)
            # Add new components
            for idx, comp in enumerate(components):
                await naming_component.create_component(
                    db,
                    naming_standard_id=standard_id,
                    file_type_id=comp["file_type_id"],
                    name=comp["name"],
                    regex=comp["regex"],
                    description=comp.get("description"),
                    order=comp.get("order", idx + 1),
                    accepted_values=comp.get("accepted_values"),
                )
            await db.commit()
            return True
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def delete_standard(db: AsyncSession, standard_id: int):
        try:
            await naming_component.delete_components_by_standard(db, standard_id)
            await project_naming_standard.delete_standard(db, standard_id)
            await db.commit()
            return True
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def get_unique_component_names_by_project(db, project_id: int):
        return await naming_component.get_unique_component_names_by_project(
            db, project_id
        )

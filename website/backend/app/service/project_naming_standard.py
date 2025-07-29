import logging

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import naming_component, project_naming_standard

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
        # Serialize components to include accepted_values
        components_serialized = [
            {
                "id": c.id,
                "naming_standard_id": c.naming_standard_id,
                "name": c.name,
                "description": c.description,
                "project_file_type_id": c.project_file_type_id,
                "regex": c.regex,
                "order": c.order,
                "accepted_values": [v.value for v in getattr(c, "accepted_values", [])],
            }
            for c in components
        ]
        return {"standard": standard, "components": components_serialized}

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
            for idx, comp in enumerate(components):
                await naming_component.create_component(
                    db,
                    naming_standard_id=standard.id,
                    project_file_type_id=project_file_type_id,
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
                "project_file_type_id": standard.project_file_type_id,
                "pattern": standard.pattern,
                "description": standard.description,
                "components": [
                    {
                        "id": c.id,
                        "name": c.name,
                        "regex": c.regex,
                        "description": c.description,
                        "order": c.order,
                        "accepted_values": [v.value for v in c.accepted_values],
                        "project_file_type_id": c.project_file_type_id,
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

            # Fetch existing components for the standard
            existing_components = await naming_component.get_components_by_standard(db, standard_id)
            existing_components_by_id = {c.id: c for c in existing_components}
            payload_ids = {c.get("id") for c in components if c.get("id") is not None}

            # Update or create components
            for idx, comp in enumerate(components):
                if comp.get("id") in existing_components_by_id:
                    # Update existing component
                    await naming_component.update_component(
                        db,
                        component_id=comp["id"],
                        update_fields={
                            "name": comp["name"],
                            "regex": comp["regex"],
                            "description": comp.get("description"),
                            "order": comp.get("order", idx + 1),
                            "project_file_type_id": comp["project_file_type_id"],
                        },
                        accepted_values=comp.get("accepted_values"),
                    )
                else:
                    # Create new component
                    await naming_component.create_component(
                        db,
                        naming_standard_id=standard_id,
                        project_file_type_id=comp["project_file_type_id"],
                        name=comp["name"],
                        regex=comp["regex"],
                        description=comp.get("description"),
                        order=comp.get("order", idx + 1),
                        accepted_values=comp.get("accepted_values"),
                    )

            # Delete removed components
            for c in existing_components:
                if c.id not in payload_ids:
                    await naming_component.delete_component(db, c.id)

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

    @staticmethod
    async def get_project_naming_standards_full(db: AsyncSession, project_id: int):
        standards = await project_naming_standard.get_standards_by_project(db, project_id)
        standards_with_components = []
        for standard in standards:
            detail = await ProjectNamingStandardService.get_standard_with_components(db, standard.id)
            standards_with_components.append(detail)
        component_names = await naming_component.get_unique_component_names_by_project(db, project_id)
        return {
            "component_names": component_names,
            "standards": standards_with_components,
        }

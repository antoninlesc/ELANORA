from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependency.database import get_db_dep
from app.crud import file_type, project_naming_standard, naming_component
from app.schema.responses.project_configuration import ProjectConfigurationResponse

router = APIRouter()


@router.get("/project/{project_id}", response_model=ProjectConfigurationResponse)
async def get_project_configuration(project_id: int, db: AsyncSession = get_db_dep):
    file_types = await file_type.get_all_file_types(db)
    standards = await project_naming_standard.get_standards_by_project(db, project_id)
    standards_with_components = []
    for std in standards:
        components = await naming_component.get_components_by_standard(db, std.id)
        standards_with_components.append(
            {
                "standard": std,
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
                    for c in components
                ],
            }
        )
    component_names = await naming_component.get_unique_component_names_by_project(
        db, project_id
    )
    return {
        "file_types": file_types,
        "standards": standards_with_components,
        "component_names": component_names,
    }

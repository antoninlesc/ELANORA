from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependency.database import get_db_dep
from app.service.file_type import FileTypeService
from app.schema.responses.file_type import FileTypeResponse
from app.schema.requests.file_type import FileTypeCreateRequest
from app.schema.requests.file_type import FileTypeUpdateRequest

router = APIRouter()


@router.get("/all", response_model=list[FileTypeResponse])
async def get_all_file_types(db: AsyncSession = get_db_dep):
    file_types = await FileTypeService.get_all_file_types(db)
    # Ensure all returned objects are serialized using the response schema
    return [FileTypeResponse.model_validate(ft) for ft in file_types]


@router.post("/", response_model=FileTypeResponse)
async def create_file_type(req: FileTypeCreateRequest, db: AsyncSession = get_db_dep):
    file_type = await FileTypeService.create_file_type(db, req.name, req.extension)
    return FileTypeResponse.model_validate(file_type)


@router.put("/{file_type_id}", response_model=FileTypeResponse)
async def update_file_type(
    file_type_id: int, req: FileTypeUpdateRequest, db: AsyncSession = get_db_dep
):
    await FileTypeService.update_file_type(
        db, file_type_id, req.model_dump(exclude_unset=True)
    )
    # Fetch the updated file type to return as response
    updated = await FileTypeService.get_all_file_types(db)
    updated_ft = next((ft for ft in updated if ft.id == file_type_id), None)
    if not updated_ft:
        raise HTTPException(status_code=404, detail="File type not found")
    return FileTypeResponse.model_validate(updated_ft)


@router.delete("/{file_type_id}", response_model=FileTypeResponse)
async def delete_file_type(file_type_id: int, db: AsyncSession = get_db_dep):
    # Fetch before delete for response
    file_types = await FileTypeService.get_all_file_types(db)
    ft = next((ft for ft in file_types if ft.id == file_type_id), None)
    if not ft:
        raise HTTPException(status_code=404, detail="File type not found")
    await FileTypeService.delete_file_type(db, file_type_id)
    return FileTypeResponse.model_validate(ft)

from app.crud import file_type as file_type_crud
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException


class FileTypeService:
    @staticmethod
    async def get_all_file_types(db):
        return await file_type_crud.get_all_file_types(db)

    @staticmethod
    async def create_file_type(db, name: str, extension: str):
        try:
            file_type = await file_type_crud.create_file_type(db, name, extension)
            await db.commit()
            return file_type
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def update_file_type(db, file_type_id: int, update_fields: dict):
        try:
            await file_type_crud.update_file_type(db, file_type_id, update_fields)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def delete_file_type(db, file_type_id: int):
        try:
            await file_type_crud.delete_file_type(db, file_type_id)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=400,
                detail="Cannot delete: This file type is used by a naming standard or component. Please delete the related naming standard first.",
            )
        except Exception:
            await db.rollback()
            raise

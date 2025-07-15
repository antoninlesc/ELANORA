"""Database utility functions for common operations."""

from typing import Any, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

ModelType = TypeVar("ModelType", bound=DeclarativeBase)


class DatabaseUtils:
    """Reusable database operation utilities."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession, model: type[ModelType], id_field: str, id_value: Any
    ) -> ModelType | None:
        """Generic get by ID function."""
        result = await db.execute(
            select(model).filter(getattr(model, id_field) == id_value)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all(db: AsyncSession, model: type[ModelType]) -> list[ModelType]:
        """Generic get all function."""
        result = await db.execute(select(model))
        return list(result.scalars().all())

    @staticmethod
    async def exists(
        db: AsyncSession, model: type[ModelType], field: str, value: Any
    ) -> bool:
        """Generic existence check."""
        result = await db.execute(
            select(getattr(model, field)).filter(getattr(model, field) == value)
        )
        return result.scalar_one_or_none() is not None

    @staticmethod
    async def create_and_commit(db: AsyncSession, instance: ModelType) -> ModelType:
        """Generic create with commit and refresh."""
        try:
            db.add(instance)
            await db.commit()
            await db.refresh(instance)
            return instance
        except Exception:
            await db.rollback()
            raise

    @staticmethod
    async def delete_by_filter(
        db: AsyncSession, model: type[ModelType], **filters
    ) -> int:
        """Generic delete with filters."""
        try:
            query = select(model)
            for field, value in filters.items():
                query = query.filter(getattr(model, field) == value)

            result = await db.execute(query)
            instances = list(result.scalars().all())
            count = len(instances)

            for instance in instances:
                await db.delete(instance)

            await db.commit()
            return count
        except Exception:
            await db.rollback()
            raise

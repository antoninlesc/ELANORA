"""Database utility functions for common operations."""

from typing import Any, TypeVar

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.core.centralized_logging import get_logger

ModelType = TypeVar("ModelType", bound=DeclarativeBase)

logger = get_logger()


class DatabaseUtils:
    """Reusable database operation utilities."""

    @staticmethod
    async def get_by_id(
        db: AsyncSession, model: type[ModelType], id_field: str, id_value: Any
    ) -> ModelType | None:
        logger.info(
            f"get_by_id: model={model.__name__} id_field={id_field} id_value={id_value}"
        )
        result = await db.execute(
            select(model).filter(getattr(model, id_field) == id_value)
        )
        instance = result.scalar_one_or_none()
        logger.debug(f"get_by_id: found={instance is not None}")
        return instance

    @staticmethod
    async def get_all(db: AsyncSession, model: type[ModelType]) -> list[ModelType]:
        logger.info(f"get_all: model={model.__name__}")
        result = await db.execute(select(model))
        all_results = list(result.scalars().all())
        logger.debug(f"get_all: count={len(all_results)}")
        return all_results

    @staticmethod
    async def exists(
        db: AsyncSession, model: type[ModelType], field: str, value: Any
    ) -> bool:
        logger.info(f"exists: model={model.__name__} field={field} value={value}")
        result = await db.execute(
            select(getattr(model, field)).filter(getattr(model, field) == value)
        )
        exists = result.scalar_one_or_none() is not None
        logger.debug(f"exists: result={exists}")
        return exists

    @staticmethod
    async def create(db: AsyncSession, instance: ModelType) -> ModelType:
        logger.info(f"create: instance={instance}")
        db.add(instance)
        return instance

    @staticmethod
    async def delete_by_filter(
        db: AsyncSession, model: type[ModelType], auto_commit: bool = False, **filters
    ) -> int:
        logger.info(f"delete_by_filter: model={model.__name__} filters={filters}")
        query = select(model)
        for field, value in filters.items():
            query = query.filter(getattr(model, field) == value)
        result = await db.execute(query)
        instances = list(result.scalars().all())
        count = len(instances)
        for instance in instances:
            await db.delete(instance)
        logger.info(f"delete_by_filter: deleted count={count}")
        return count

    @staticmethod
    async def bulk_insert(
        db: AsyncSession,
        model: type[ModelType],
        values: list[dict],
        ignore_duplicates: bool = False,
    ) -> None:
        """Bulk insert records. If ignore_duplicates is True, uses MySQL ON DUPLICATE KEY UPDATE."""
        from sqlalchemy.dialects.mysql import insert as mysql_insert

        stmt = mysql_insert(model).values(values)
        if ignore_duplicates:
            pk_names = [key.name for key in model.__table__.primary_key]
            update_cols = {
                c.name: stmt.inserted[c.name]
                for c in model.__table__.columns
                if c.name not in pk_names
            }
            stmt = stmt.on_duplicate_key_update(**update_cols)
        await db.execute(stmt)

    @staticmethod
    async def update_by_filter(
        db: AsyncSession, model: type[ModelType], filters: dict, update_fields: dict
    ) -> int:
        """Update records matching filters with update_fields. Returns number of updated rows."""
        query = update(model)
        for field, value in filters.items():
            query = query.where(getattr(model, field) == value)
        query = query.values(**update_fields)
        result = await db.execute(query)
        return result.rowcount

    @staticmethod
    async def get_by_filter(
        db: AsyncSession,
        model: type[ModelType],
        filters: dict,
        order_by: list | None = None,
    ) -> list[ModelType]:
        """Get records matching filters, optionally ordered."""
        query = select(model)
        for field, value in filters.items():
            if isinstance(value, list):
                query = query.where(getattr(model, field).in_(tuple(value)))
            else:
                query = query.where(getattr(model, field) == value)
        if order_by:
            query = query.order_by(*order_by)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_one_by_filter(
        db: AsyncSession,
        model: type[ModelType],
        filters: dict,
        order_by: list | None = None,
    ) -> ModelType | None:
        """Get a single record matching filters, optionally ordered."""
        query = select(model)
        for field, value in filters.items():
            if isinstance(value, list):
                query = query.where(getattr(model, field).in_(tuple(value)))
            else:
                query = query.where(getattr(model, field) == value)
        if order_by:
            query = query.order_by(*order_by)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def paginate(
        db: AsyncSession,
        model: type[ModelType],
        page: int,
        page_size: int,
        filters: dict | None,
    ) -> list[ModelType]:
        """Paginate records with optional filters."""
        query = select(model)
        filters = filters or {}
        for field, value in filters.items():
            if isinstance(value, list):
                query = query.where(getattr(model, field).in_(tuple(value)))
            else:
                query = query.where(getattr(model, field) == value)
        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def count(
        db: AsyncSession, model: type[ModelType], filters: dict | None
    ) -> int:
        """Count records matching optional filters."""
        query = select(func.count()).select_from(model)
        filters = filters or {}
        for field, value in filters.items():
            if isinstance(value, list):
                query = query.where(getattr(model, field).in_(tuple(value)))
            else:
                query = query.where(getattr(model, field) == value)
        result = await db.execute(query)
        return result.scalar_one()

    @staticmethod
    async def bulk_delete(
        db: AsyncSession, model: type[ModelType], where_clause
    ) -> int:
        """Bulk delete records matching the given where_clause.
        Returns the number of deleted rows.
        """
        result = await db.execute(delete(model).where(where_clause))
        logger.info(f"bulk_delete: model={model.__name__} deleted={result.rowcount}")
        return result.rowcount if result.rowcount is not None else 0

    @staticmethod
    async def bulk_update(
        db: AsyncSession,
        model: type[ModelType],
        data: list[dict],
        pk_field: str,
    ) -> int:
        """Bulk update records for the given model.
        Each dict in data must include the primary key field.
        Returns the number of updated rows.
        """
        if not data:
            return 0
        total = 0
        for row in data:
            pk_value = row[pk_field]
            update_data = {k: v for k, v in row.items() if k != pk_field}
            result = await db.execute(
                update(model)
                .where(getattr(model, pk_field) == pk_value)
                .values(**update_data)
            )
            total += result.rowcount if result.rowcount else 0
        logger.info(f"bulk_update: model={model.__name__} updated={total}")
        return total

    @staticmethod
    async def get_orphaned_by_association(
        db: AsyncSession,
        main_model: type[ModelType],
        assoc_model: type[ModelType],
        main_id_field: str,
        assoc_main_id_field: str,
        assoc_parent_field: str,
        parent_id: int,
    ) -> list[ModelType]:
        """Fetch instances from main_model that are linked in assoc_model
        only to the given parent_id (via assoc_parent_field), and to no other parent.
        """
        main_id_col = getattr(main_model, main_id_field)
        assoc_main_id_col = getattr(assoc_model, assoc_main_id_field)
        assoc_parent_col = getattr(assoc_model, assoc_parent_field)

        stmt = (
            select(main_model)
            .join(assoc_model, assoc_main_id_col == main_id_col)
            .group_by(main_id_col)
            .having(
                func.count(assoc_parent_col) == 1,
                func.max(assoc_parent_col) == parent_id,
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_fully_orphaned(
        db,
        main_model,
        assoc_model,
        main_id_field: str,
        assoc_ref_field: str,
    ):
        """
        Return all main_model records whose main_id_field is NOT referenced in assoc_model.assoc_ref_field.
        """
        main_id_col = getattr(main_model, main_id_field)
        assoc_ref_col = getattr(assoc_model, assoc_ref_field)
        subq = select(assoc_ref_col).distinct()
        query = select(main_model).where(~main_id_col.in_(subq))
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def delete_fully_orphaned(
        db,
        main_model,
        assoc_model,
        main_id_field: str,
        assoc_ref_field: str,
    ) -> int:
        """
        Delete all main_model records whose main_id_field is NOT referenced in assoc_model.assoc_ref_field.
        Returns the number of deleted rows.
        """
        orphans = await DatabaseUtils.get_fully_orphaned(
            db, main_model, assoc_model, main_id_field, assoc_ref_field
        )
        count = len(orphans)
        for orphan in orphans:
            await db.delete(orphan)
        return count

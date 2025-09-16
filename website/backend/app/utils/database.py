"""Database utility functions for common operations."""

from collections.abc import Sequence
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
        db: AsyncSession,
        model: type[ModelType],
        id_field: str,
        id_value: Any,
        options: list | None = None,
    ) -> ModelType | None:
        logger.info(
            f"get_by_id: model={model.__name__} id_field={id_field} id_value={id_value}"
        )
        query = select(model).filter(getattr(model, id_field) == id_value)
        if options:
            for opt in options:
                query = query.options(opt)
        result = await db.execute(query)
        instance = result.scalar_one_or_none()
        logger.debug(f"get_by_id: found={instance is not None}")
        return instance

    @staticmethod
    async def get_all(
        db: AsyncSession, model: type[ModelType], options: list | None = None
    ) -> list[ModelType]:
        logger.info(f"get_all: model={model.__name__}")
        query = select(model)
        if options:
            for opt in options:
                query = query.options(opt)
        result = await db.execute(query)
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
    async def delete_by_conditions(
        db: AsyncSession, model: type[ModelType], conditions: list[Any] | None = None
    ) -> int:
        """Delete records matching SQLAlchemy conditions (AND/OR expressions)."""
        logger.info(
            f"delete_by_conditions: model={model.__name__} conditions={conditions}"
        )
        query = select(model)
        if conditions:
            from sqlalchemy import and_

            query = query.where(and_(*conditions))
        result = await db.execute(query)
        instances = list(result.scalars().all())
        count = len(instances)
        for instance in instances:
            await db.delete(instance)
        logger.info(f"delete_by_conditions: deleted count={count}")
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
        options: list | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ModelType]:
        """Get records matching filters with optional ordering and pagination."""
        query = select(model)
        for field, value in filters.items():
            if isinstance(value, list):
                query = query.where(getattr(model, field).in_(tuple(value)))
            else:
                query = query.where(getattr(model, field) == value)
        if order_by:
            query = query.order_by(*order_by)
        if options:
            for opt in options:
                query = query.options(opt)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_conditions(
        db: AsyncSession,
        model: type[ModelType],
        conditions: list[Any] | None = None,
        order_by: list | None = None,
        options: list | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ModelType]:
        """Get records matching SQLAlchemy conditions (AND/OR expressions)."""
        query = select(model)
        if conditions:
            from sqlalchemy import and_

            query = query.where(and_(*conditions))
        if order_by:
            query = query.order_by(*order_by)
        if options:
            for opt in options:
                query = query.options(opt)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_with_relationships(
        db: AsyncSession,
        model: type[ModelType],
        relationships: list[tuple[str, Any]] | None = None,
        filters: dict | None = None,
        conditions: list[Any] | None = None,
        order_by: list | None = None,
        options: list | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ModelType]:
        """Get records with relationship joins and filtering."""
        query = select(model)

        # Apply joins for relationships
        if relationships:
            for relationship_name, join_condition in relationships:
                if hasattr(model, relationship_name):
                    # Use relationship-based join if available
                    query = query.join(getattr(model, relationship_name))
                else:
                    # Use explicit join condition
                    query = query.join(join_condition)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    query = query.where(getattr(model, field).in_(tuple(value)))
                else:
                    query = query.where(getattr(model, field) == value)

        # Apply conditions
        if conditions:
            from sqlalchemy import and_

            query = query.where(and_(*conditions))

        if order_by:
            query = query.order_by(*order_by)
        if options:
            for opt in options:
                query = query.options(opt)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_aggregated_data(
        db: AsyncSession,
        model: type[ModelType],
        aggregates: dict[str, Any],
        group_by: list | None = None,
        filters: dict | None = None,
        conditions: list[Any] | None = None,
        having_conditions: list[Any] | None = None,
    ) -> list[dict]:
        """Get aggregated data with optional grouping and filtering."""
        # Build select clause with aggregates
        select_items = []
        if group_by:
            select_items.extend(group_by)

        for alias, agg_func in aggregates.items():
            select_items.append(agg_func.label(alias))

        query = select(*select_items).select_from(model)

        # Apply filters
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    query = query.where(getattr(model, field).in_(tuple(value)))
                else:
                    query = query.where(getattr(model, field) == value)

        # Apply conditions
        if conditions:
            from sqlalchemy import and_

            query = query.where(and_(*conditions))

        # Group by
        if group_by:
            query = query.group_by(*group_by)

        # Having conditions
        if having_conditions:
            from sqlalchemy import and_

            query = query.having(and_(*having_conditions))

        result = await db.execute(query)
        return [dict(row) for row in result.all()]

    @staticmethod
    async def get_with_exists_conditions(
        db: AsyncSession,
        model: type[ModelType],
        exists_conditions: list[tuple[type[ModelType], dict]] | None = None,
        not_exists_conditions: list[tuple[type[ModelType], dict]] | None = None,
        filters: dict | None = None,
        conditions: list[Any] | None = None,
        order_by: list | None = None,
        options: list | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[ModelType]:
        """Get records with EXISTS/NOT EXISTS subquery conditions."""
        from sqlalchemy import exists

        query = select(model)

        # Apply EXISTS conditions
        if exists_conditions:
            for related_model, subquery_filters in exists_conditions:
                subquery = select(related_model)
                for field, value in subquery_filters.items():
                    if isinstance(value, list):
                        subquery = subquery.where(
                            getattr(related_model, field).in_(tuple(value))
                        )
                    else:
                        subquery = subquery.where(
                            getattr(related_model, field) == value
                        )
                query = query.where(exists(subquery))

        # Apply NOT EXISTS conditions
        if not_exists_conditions:
            for related_model, subquery_filters in not_exists_conditions:
                subquery = select(related_model)
                for field, value in subquery_filters.items():
                    if isinstance(value, list):
                        subquery = subquery.where(
                            getattr(related_model, field).in_(tuple(value))
                        )
                    else:
                        subquery = subquery.where(
                            getattr(related_model, field) == value
                        )
                query = query.where(~exists(subquery))

        # Apply filters
        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    query = query.where(getattr(model, field).in_(tuple(value)))
                else:
                    query = query.where(getattr(model, field) == value)

        # Apply conditions
        if conditions:
            from sqlalchemy import and_

            query = query.where(and_(*conditions))

        if order_by:
            query = query.order_by(*order_by)
        if options:
            for opt in options:
                query = query.options(opt)
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())

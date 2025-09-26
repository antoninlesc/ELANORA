"""Database utility functions for common operations."""

from datetime import datetime, timezone
from typing import Any, TypeVar

from sqlalchemy import and_, delete, exists, func, select, update
from sqlalchemy.dialects.mysql import insert as mysql_insert
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
        """Get a single record by ID field."""
        logger.info(
            f"get_by_id: model={model.__name__} id_field={id_field} id_value={id_value}"
        )
        query = select(model).where(getattr(model, id_field) == id_value)
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
        """Get all records of the model."""
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
        """Check if a record exists with the given field value."""
        logger.info(f"exists: model={model.__name__} field={field} value={value}")
        result = await db.execute(
            select(1).where(getattr(model, field) == value).limit(1)
        )
        exists = result.scalar_one_or_none() is not None
        logger.debug(f"exists: result={exists}")
        return exists

    @staticmethod
    async def create(db: AsyncSession, instance: ModelType) -> ModelType:
        """Add a new instance to the session."""
        logger.info(f"create: instance={instance}")
        db.add(instance)
        return instance

    @staticmethod
    async def get_one_or_none(
        db: AsyncSession,
        model: type[ModelType],
        filters: dict | None = None,
        conditions: list[Any] | None = None,
        options: list | None = None,
    ) -> ModelType | None:
        """Get exactly one record or None if not found."""
        query = select(model)

        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    query = query.where(getattr(model, field).in_(tuple(value)))
                else:
                    query = query.where(getattr(model, field) == value)

        if conditions:
            query = query.where(and_(*conditions))

        if options:
            for opt in options:
                query = query.options(opt)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_scalar_subquery(
        db: AsyncSession,
        model: type[ModelType],
        field: str,
        filters: dict | None = None,
        conditions: list[Any] | None = None,
    ) -> Any:
        """Get a scalar value from a subquery (useful for EXISTS checks, counts, etc.)."""
        query = select(getattr(model, field))

        if filters:
            for f, value in filters.items():
                query = query.where(getattr(model, f) == value)

        if conditions:
            query = query.where(and_(*conditions))

        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def count_records(
        db: AsyncSession,
        model: type[ModelType],
        filters: dict | None = None,
        conditions: list[Any] | None = None,
    ) -> int:
        """Count records matching filters or conditions."""
        query = select(func.count()).select_from(model)

        if filters:
            for field, value in filters.items():
                if isinstance(value, list):
                    query = query.where(getattr(model, field).in_(tuple(value)))
                else:
                    query = query.where(getattr(model, field) == value)

        if conditions:
            query = query.where(and_(*conditions))

        result = await db.execute(query)
        return result.scalar() or 0

    @staticmethod
    async def upsert(
        db: AsyncSession,
        model: type[ModelType],
        defaults: dict,
        **lookup_fields,
    ) -> tuple[ModelType, bool]:
        """Get or create a record. Returns (instance, created)."""
        # Try to get existing record
        existing = await DatabaseUtils.get_one_or_none(db, model, filters=lookup_fields)

        if existing:
            # Update with defaults if provided
            if defaults:
                for key, value in defaults.items():
                    setattr(existing, key, value)
            return existing, False

        # Create new record
        all_fields = {**lookup_fields, **defaults}
        new_instance = model(**all_fields)
        await DatabaseUtils.create(db, new_instance)
        return new_instance, True

    @staticmethod
    async def delete_by_filter(
        db: AsyncSession, model: type[ModelType], auto_commit: bool = False, **filters
    ) -> int:
        """Delete records matching the filters."""
        logger.info(f"delete_by_filter: model={model.__name__} filters={filters}")
        stmt = delete(model)
        for field, value in filters.items():
            stmt = stmt.where(getattr(model, field) == value)
        result = await db.execute(stmt)
        count = result.rowcount
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
        stmt = delete(model)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        result = await db.execute(stmt)
        count = result.rowcount
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
            query = query.where(and_(*conditions))

        # Group by
        if group_by:
            query = query.group_by(*group_by)

        # Having conditions
        if having_conditions:
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

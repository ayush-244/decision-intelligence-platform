"""Declarative base and shared naming conventions for ORM models.

An explicit constraint naming convention is defined up-front because Alembic
autogenerate relies on deterministic names to produce stable, reviewable
migrations. Establishing this before any table exists prevents a painful
retrofit later.
"""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Consistent constraint names -> deterministic Alembic migrations.
NAMING_CONVENTION: dict[str, str] = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base class for all ORM models.

    Future domain models will subclass this. Kept intentionally minimal in the
    foundation phase — only the shared metadata/naming convention is defined.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

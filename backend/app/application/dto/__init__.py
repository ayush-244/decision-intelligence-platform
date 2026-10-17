"""Data-transfer objects passed across the application boundary.

DTOs are plain, immutable dataclasses — deliberately free of framework types so
the application layer stays portable. The presentation layer maps them to/from
its own Pydantic schemas.
"""

from app.application.dto.system import SystemInfo

__all__ = ["SystemInfo"]

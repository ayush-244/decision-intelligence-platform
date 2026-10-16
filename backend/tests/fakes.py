"""In-process test doubles implementing domain ports.

Using real interface implementations (rather than mocks) keeps tests coupled to
the *contract*, not to call internals, so refactors don't break the suite.
"""

from __future__ import annotations

import asyncio

from app.domain.entities.health import ComponentHealth, HealthStatus
from app.domain.ports.health_probe import HealthProbe


class FakeHealthProbe(HealthProbe):
    """A configurable :class:`HealthProbe` for tests."""

    def __init__(
        self,
        name: str,
        status: HealthStatus = HealthStatus.HEALTHY,
        *,
        detail: str | None = None,
        delay_seconds: float = 0.0,
        raises: Exception | None = None,
    ) -> None:
        self._name = name
        self._status = status
        self._detail = detail
        self._delay_seconds = delay_seconds
        self._raises = raises

    @property
    def component_name(self) -> str:
        return self._name

    async def check(self) -> ComponentHealth:
        if self._delay_seconds:
            await asyncio.sleep(self._delay_seconds)
        if self._raises is not None:
            raise self._raises
        return ComponentHealth(name=self._name, status=self._status, detail=self._detail)

"""Service exposing static service metadata (name, version, environment)."""

from __future__ import annotations

from app import __version__
from app.application.dto.system import SystemInfo
from app.core.config import Settings


class SystemInfoService:
    """Assembles :class:`SystemInfo` from configuration and package metadata.

    Kept as an injectable service (rather than a module function) so the
    version source can evolve — e.g. reading a build SHA — without changing
    consumers.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def get_info(self) -> SystemInfo:
        """Return the current service identity snapshot."""
        return SystemInfo(
            name=self._settings.app_name,
            version=__version__,
            environment=self._settings.environment.value,
        )

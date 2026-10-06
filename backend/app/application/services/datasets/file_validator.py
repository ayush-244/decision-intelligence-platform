"""Pre-storage file validation."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.config import Settings
from app.domain.value_objects.data_source import DataSourceFormat
from app.shared.exceptions import BusinessValidationError


@dataclass(frozen=True, slots=True)
class FileValidationResult:
    format: DataSourceFormat
    size_bytes: int
    checks: dict[str, bool]
    warnings: tuple[str, ...]


class UploadFileValidator:
    """Validate uploads before they touch storage or Polars."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def validate(
        self,
        *,
        filename: str,
        content_type: str | None,
        data: bytes,
    ) -> FileValidationResult:
        warnings: list[str] = []
        if not data:
            raise BusinessValidationError("Uploaded file is empty.")

        size = len(data)
        if size > self._settings.max_upload_size_bytes:
            max_mb = self._settings.max_upload_size_bytes // (1024 * 1024)
            raise BusinessValidationError(f"File exceeds maximum upload size of {max_mb} MiB.")

        source_format = DataSourceFormat.from_filename(filename)
        if source_format is None:
            raise BusinessValidationError("Unsupported file type. Use CSV, XLSX, or Parquet.")

        if content_type and content_type not in source_format.mime_types:
            warnings.append(f"Content-Type '{content_type}' does not match expected format.")

        checks = {
            "size_within_limit": True,
            "format_supported": True,
            "non_empty": True,
        }
        return FileValidationResult(
            format=source_format,
            size_bytes=size,
            checks=checks,
            warnings=tuple(warnings),
        )

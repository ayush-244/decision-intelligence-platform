"""Unit tests for upload file validation."""

from __future__ import annotations

import pytest

from app.application.services.datasets.file_validator import UploadFileValidator
from app.core.config import Settings
from app.shared.exceptions import BusinessValidationError

pytestmark = pytest.mark.unit


def test_rejects_empty_file() -> None:
    validator = UploadFileValidator(Settings())
    with pytest.raises(BusinessValidationError, match="empty"):
        validator.validate(filename="data.csv", content_type="text/csv", data=b"")


def test_rejects_unsupported_extension() -> None:
    validator = UploadFileValidator(Settings())
    with pytest.raises(BusinessValidationError, match="Unsupported"):
        validator.validate(filename="data.json", content_type="application/json", data=b"{}")


def test_accepts_csv_file() -> None:
    validator = UploadFileValidator(Settings())
    result = validator.validate(
        filename="sales.csv",
        content_type="text/csv",
        data=b"name,value\na,1\n",
    )
    assert result.format.value == "csv"
    assert result.size_bytes > 0

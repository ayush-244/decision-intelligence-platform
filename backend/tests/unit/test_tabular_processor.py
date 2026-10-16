"""Unit tests for tabular schema inference."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import Settings
from app.domain.value_objects.column_type import ColumnSemanticType
from app.domain.value_objects.data_source import DataSourceFormat
from app.infrastructure.processing.tabular_processor import TabularProcessor

pytestmark = pytest.mark.unit

_SAMPLE_CSV = b"id,name,amount,active\n1,Alice,10.5,true\n2,Bob,20.0,false\n"


def test_profile_csv_file(tmp_path: Path) -> None:
    path = tmp_path / "sample.csv"
    path.write_bytes(_SAMPLE_CSV)
    processor = TabularProcessor(Settings())
    profile = processor.profile_file(path=path, source_format=DataSourceFormat.CSV)
    assert profile.row_count == 2
    assert len(profile.columns) == 4
    assert profile.columns[0].semantic_type in {
        ColumnSemanticType.INTEGER,
        ColumnSemanticType.IDENTIFIER,
    }
    assert len(profile.preview_rows) == 2

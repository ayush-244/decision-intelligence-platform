"""Serialize causal DTOs to JSON-compatible dicts."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

import numpy as np


def to_jsonable(value: Any) -> Any:
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        f = float(value)
        if f != f or f in {float("inf"), float("-inf")}:
            return None
        return f
    if isinstance(value, np.ndarray):
        return [to_jsonable(item) for item in value.tolist()]
    if is_dataclass(value) and not isinstance(value, type):
        return {key: to_jsonable(val) for key, val in asdict(value).items()}
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, float) and (value != value or value in {float("inf"), float("-inf")}):
        return None
    return value

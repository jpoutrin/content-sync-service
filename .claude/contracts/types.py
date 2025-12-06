"""
Shared domain types for all parallel agents.

IMPORTANT: Changes here affect ALL parallel tasks.
Coordinate before modifying.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import TypedDict


# === Entities ===
# Define shared domain entities here


# === Enums ===
# Define shared enums here


# === API Types ===
class PaginationMeta(TypedDict):
    page: int
    total: int
    per_page: int


class ApiResponse(TypedDict):
    data: dict | list
    meta: PaginationMeta | None


class ApiError(TypedDict):
    code: str
    message: str
    details: dict | None

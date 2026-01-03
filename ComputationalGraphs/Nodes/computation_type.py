"""ComputationType enum and helpers.

Provide explicit enum members for node computation types and light helper
functions for backwards-compatible conversions from legacy string values.
"""

from enum import Enum
from typing import Union


class ComputationType(Enum):
    """Enumeration for node computation types.

    Members:
        BASIC: simple single-operation nodes (e.g., AdditionNode)
        COMPLEX: composite/compound nodes (e.g., AbstractNode, CompressedNode)
    """

    BASIC = "basic"
    COMPLEX = "complex"


def to_enum(value: Union[str, "ComputationType"]) -> "ComputationType":
    """Convert a string or ComputationType to a ComputationType enum.

    Accepts legacy strings (case-insensitive) and returns the corresponding
    enum member. If an unknown string is provided, ValueError is raised.
    """
    if isinstance(value, ComputationType):
        return value
    if not isinstance(value, str):
        raise TypeError("ComputationType must be created from str or ComputationType")
    val = value.strip().lower()
    if val == "basic":
        return ComputationType.BASIC
    if val == "complex":
        return ComputationType.COMPLEX
    raise ValueError(f"Unknown computation type: {value!r}")


def to_value(value: Union[str, "ComputationType"]) -> str:
    """Return the string value for a ComputationType or a legacy string input.

    This is useful for serializing enums as plain strings to preserve
    compatibility with existing saved graphs.
    """
    if isinstance(value, ComputationType):
        return value.value
    if isinstance(value, str):
        # validate by converting
        return to_enum(value).value
    raise TypeError("ComputationType value must be str or ComputationType")


__all__ = ["ComputationType", "to_enum", "to_value"]

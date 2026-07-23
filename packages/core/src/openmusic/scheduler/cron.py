"""Cron expression parsing and validation for the scheduling system.

Supports standard 5-field cron expressions:
    ┌──────── minute (0-59)
    │ ┌────── hour (0-23)
    │ │ ┌──── day of month (1-31)
    │ │ │ ┌── month (1-12)
    │ │ │ │ ┌ day of week (0-7, 0=Sun, 7=Sun)
    │ │ │ │ │
    * * * * *
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List


class CronParseError(ValueError):
    """Raised when a cron expression cannot be parsed."""

    pass


@dataclass(frozen=True)
class CronExpression:
    """A parsed, validated 5-field cron expression."""

    minute: str
    hour: str
    day_of_month: str
    month: str
    day_of_week: str

    def __str__(self) -> str:
        return f"{self.minute} {self.hour} {self.day_of_month} {self.month} {self.day_of_week}"

    def to_crontab_line(self, command: str, comment: str = "") -> str:
        """Format as a crontab entry line."""
        line = str(self)
        if command:
            line += f" {command}"
        if comment:
            line += f" # {comment}"
        return line


# Field ranges for validation
_FIELD_RANGES: dict[str, tuple[int, int]] = {
    "minute": (0, 59),
    "hour": (0, 23),
    "day_of_month": (1, 31),
    "month": (1, 12),
    "day_of_week": (0, 7),
}

_FIELD_NAMES = ["minute", "hour", "day_of_month", "month", "day_of_week"]

# Predefined aliases
_ALIASES: dict[str, str] = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}


def _expand_field(field: str, field_name: str) -> str:
    """Validate and normalize a single cron field."""
    low, high = _FIELD_RANGES[field_name]

    # Handle step values: */5, 1-10/2
    step_match = re.match(r"^(\S+)/(\d+)$", field)
    if step_match:
        range_part = step_match.group(1)
        step = int(step_match.group(2))
        if step < 1:
            raise CronParseError(f"Step value must be >= 1 in field '{field_name}': {field}")
        _expand_field(range_part, field_name)
        return field

    # Handle ranges: 1-5
    range_match = re.match(r"^(\d+)-(\d+)$", field)
    if range_match:
        start, end = int(range_match.group(1)), int(range_match.group(2))
        if start < low or end > high or start > end:
            raise CronParseError(
                f"Invalid range in field '{field_name}': {field} "
                f"(expected {low}-{high})"
            )
        return field

    # Handle wildcard
    if field == "*":
        return field

    # Handle lists: 1,3,5
    if "," in field:
        parts = [p.strip() for p in field.split(",")]
        for part in parts:
            _expand_field(part, field_name)
        return field

    # Handle plain number
    try:
        val = int(field)
    except ValueError:
        raise CronParseError(
            f"Invalid cron field '{field_name}': {field}"
        ) from None

    if val < low or val > high:
        raise CronParseError(
            f"Value {val} out of range for field '{field_name}' "
            f"(expected {low}-{high})"
        )
    return field


def validate_cron(expression: str) -> CronExpression:
    """Parse and validate a cron expression string.

    Supports standard 5-field cron expressions and predefined aliases
    like @daily, @hourly, @weekly, @monthly, @yearly.

    Args:
        expression: A cron expression string (e.g., "0 2 * * 5" or "@daily").

    Returns:
        A CronExpression instance.

    Raises:
        CronParseError: If the expression is invalid.
    """
    expression = expression.strip()
    if expression.startswith("@"):
        expanded = _ALIASES.get(expression)
        if expanded is None:
            raise CronParseError(
                f"Unknown cron alias: '{expression}'. "
                f"Supported: {', '.join(sorted(_ALIASES.keys()))}"
            )
        expression = expanded

    parts = expression.strip().split()
    if len(parts) != 5:
        raise CronParseError(
            f"Cron expression must have exactly 5 fields, got {len(parts)}: '{expression}'"
        )

    fields: List[str] = []
    for name, part in zip(_FIELD_NAMES, parts):
        fields.append(_expand_field(part.strip(), name))

    return CronExpression(
        minute=fields[0],
        hour=fields[1],
        day_of_month=fields[2],
        month=fields[3],
        day_of_week=fields[4],
    )

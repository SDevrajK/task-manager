"""Smart date parsing for natural language dates."""

from datetime import datetime, timedelta
from typing import Optional
import re


class DateParser:
    """Parse natural language dates."""

    # Common date patterns
    PATTERNS = {
        r"^tomorrow$": lambda: datetime.now() + timedelta(days=1),
        r"^today$": lambda: datetime.now(),
        r"^next\s+monday$": lambda: _next_weekday(0),
        r"^next\s+tuesday$": lambda: _next_weekday(1),
        r"^next\s+wednesday$": lambda: _next_weekday(2),
        r"^next\s+thursday$": lambda: _next_weekday(3),
        r"^next\s+friday$": lambda: _next_weekday(4),
        r"^next\s+saturday$": lambda: _next_weekday(5),
        r"^next\s+sunday$": lambda: _next_weekday(6),
        r"^monday$": lambda: _next_weekday(0),
        r"^tuesday$": lambda: _next_weekday(1),
        r"^wednesday$": lambda: _next_weekday(2),
        r"^thursday$": lambda: _next_weekday(3),
        r"^friday$": lambda: _next_weekday(4),
        r"^saturday$": lambda: _next_weekday(5),
        r"^sunday$": lambda: _next_weekday(6),
        r"^in\s+(\d+)\s+days?$": lambda m: datetime.now() + timedelta(days=int(m.group(1))),
        r"^in\s+(\d+)\s+weeks?$": lambda m: datetime.now() + timedelta(weeks=int(m.group(1))),
        r"^in\s+(\d+)\s+months?$": lambda m: datetime.now() + timedelta(days=30 * int(m.group(1))),
        r"^(\d+)\s+days?(?:\s+from\s+now)?$": lambda m: datetime.now() + timedelta(days=int(m.group(1))),
        r"^(\d+)\s+weeks?(?:\s+from\s+now)?$": lambda m: datetime.now() + timedelta(weeks=int(m.group(1))),
        r"^next\s+week$": lambda: datetime.now() + timedelta(weeks=1),
        r"^next\s+month$": lambda: datetime.now() + timedelta(days=30),
    }

    @staticmethod
    def parse(date_str: str) -> Optional[str]:
        """Parse date string to YYYY-MM-DD format.

        Supports:
        - ISO format: 2026-01-08
        - Natural language: tomorrow, next wednesday, in 3 days, etc.

        Returns YYYY-MM-DD or None if parsing fails.
        """
        if not date_str:
            return None

        date_str = date_str.strip().lower()

        # Try ISO format first
        try:
            parsed = datetime.strptime(date_str, "%Y-%m-%d")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            pass

        # Try natural language patterns
        for pattern, parser in DateParser.PATTERNS.items():
            match = re.match(pattern, date_str)
            if match:
                try:
                    if match.groups():
                        result_date = parser(match)
                    else:
                        result_date = parser()
                    return result_date.strftime("%Y-%m-%d")
                except (ValueError, IndexError, AttributeError):
                    continue

        return None

    @staticmethod
    def parse_or_raise(date_str: str) -> str:
        """Parse date or raise ValueError with helpful message."""
        result = DateParser.parse(date_str)
        if result is None:
            raise ValueError(
                f"Could not parse date: '{date_str}'. "
                "Use YYYY-MM-DD or natural language like 'tomorrow', "
                "'next friday', 'in 3 days'"
            )
        return result


def _next_weekday(target_day: int) -> datetime:
    """Get the next occurrence of target weekday (0=Monday, 6=Sunday)."""
    today = datetime.now()
    current_day = today.weekday()

    # If today is the target day, return today + 1 week
    # Otherwise, return the next occurrence
    days_ahead = target_day - current_day
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7
    elif days_ahead == 0:  # Today is the target day
        days_ahead = 7

    return today + timedelta(days=days_ahead)

"""Pure scheduling logic. No Telegram and no database, so it is easy to test."""

from __future__ import annotations

import calendar
from datetime import date, datetime, time, timedelta

Interval = tuple[datetime, datetime]


def overlaps(a: Interval, b: Interval) -> bool:
    return a[0] < b[1] and b[0] < a[1]


def free_slots(
    day: date,
    hours: tuple[time, time] | None,
    duration: timedelta,
    busy: list[Interval],
    now: datetime,
    step: timedelta = timedelta(minutes=30),
    min_lead: timedelta = timedelta(minutes=60),
) -> list[datetime]:
    """Start times on `day` where an appointment of `duration` fits.

    A slot is free when it lies inside opening hours, starts at least
    `min_lead` after `now` and does not overlap any busy interval.
    """
    if hours is None:
        return []
    opens = datetime.combine(day, hours[0])
    closes = datetime.combine(day, hours[1])
    earliest = now + min_lead

    slots = []
    start = opens
    while start + duration <= closes:
        candidate = (start, start + duration)
        if start >= earliest and not any(overlaps(candidate, b) for b in busy):
            slots.append(start)
        start += step
    return slots


def month_grid(year: int, month: int) -> list[list[date | None]]:
    """Weeks of the month (Monday first); days of other months are None."""
    weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
    return [[d if d.month == month else None for d in week] for week in weeks]


def shift_month(year: int, month: int, delta: int) -> tuple[int, int]:
    index = year * 12 + (month - 1) + delta
    return index // 12, index % 12 + 1

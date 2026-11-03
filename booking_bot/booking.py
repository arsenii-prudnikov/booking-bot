"""Booking rules that combine the database, the settings and the scheduling logic."""

from __future__ import annotations

from datetime import date, datetime, timedelta

from . import config
from .config import Settings
from .db import Database
from .scheduling import free_slots


class BookingService:
    def __init__(self, db: Database, settings: Settings) -> None:
        self.db = db
        self.settings = settings

    def now(self) -> datetime:
        """Current local time of the business, without tzinfo (as stored in the DB)."""
        return datetime.now(self.settings.tz).replace(tzinfo=None, second=0, microsecond=0)

    def bookable_range(self) -> tuple[date, date]:
        today = self.now().date()
        return today, today + timedelta(days=config.BOOKING_HORIZON_DAYS)

    def slots(self, day: date, service_id: str, exclude_id: int | None = None) -> list[datetime]:
        first, last = self.bookable_range()
        if not first <= day <= last or self.db.is_closed(day):
            return []
        return free_slots(
            day=day,
            hours=config.OPENING_HOURS.get(day.weekday()),
            duration=timedelta(minutes=config.SERVICES[service_id].duration_min),
            busy=self.db.busy_on(day, exclude_id),
            now=self.now(),
            step=timedelta(minutes=config.SLOT_STEP_MIN),
            min_lead=timedelta(minutes=config.MIN_LEAD_MIN),
        )

    def available_days(self, days: list[date], service_id: str, exclude_id: int | None = None) -> set[date]:
        return {d for d in days if self.slots(d, service_id, exclude_id)}

    def end_of(self, start: datetime, service_id: str) -> datetime:
        return start + timedelta(minutes=config.SERVICES[service_id].duration_min)

    def book(self, user_id: int, service_id: str, start: datetime) -> int | None:
        if start not in self.slots(start.date(), service_id):
            return None
        return self.db.create_booking(user_id, service_id, start, self.end_of(start, service_id), self.now())

    def move(self, booking_id: int, start: datetime) -> bool:
        booking = self.db.get_booking(booking_id)
        if booking is None or booking.status != "active":
            return False
        if start not in self.slots(start.date(), booking.service, exclude_id=booking_id):
            return False
        return self.db.reschedule(booking_id, start, self.end_of(start, booking.service), self.now())

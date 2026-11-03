from datetime import date, datetime, time, timedelta

import pytest

from booking_bot.booking import BookingService
from booking_bot.config import Settings
from booking_bot.db import Database
from booking_bot.scheduling import free_slots, month_grid, shift_month

MONDAY = date(2026, 11, 9)
NOW = datetime(2026, 11, 6, 12, 0)  # Friday before


class FixedClockService(BookingService):
    def now(self) -> datetime:
        return NOW


@pytest.fixture
def service(tmp_path):
    db = Database(str(tmp_path / "test.db"))
    return FixedClockService(db, Settings(token="x", owner_chat_id=None))


# ---------- scheduling ----------

def test_free_slots_respect_opening_hours_and_duration():
    slots = free_slots(MONDAY, (time(9), time(11)), timedelta(minutes=50), [], NOW)
    assert [s.strftime("%H:%M") for s in slots] == ["09:00", "09:30", "10:00"]


def test_free_slots_skip_busy_intervals():
    busy = [(datetime(2026, 11, 9, 9, 30), datetime(2026, 11, 9, 10, 0))]
    slots = free_slots(MONDAY, (time(9), time(11)), timedelta(minutes=30), busy, NOW)
    assert [s.strftime("%H:%M") for s in slots] == ["09:00", "10:00", "10:30"]


def test_free_slots_need_lead_time():
    now = datetime(2026, 11, 9, 9, 10)
    slots = free_slots(MONDAY, (time(9), time(12)), timedelta(minutes=30), [], now)
    assert slots[0].strftime("%H:%M") == "10:30"


def test_closed_day_has_no_slots():
    assert free_slots(MONDAY, None, timedelta(minutes=30), [], NOW) == []


def test_month_grid_and_shift():
    grid = month_grid(2026, 11)
    assert grid[0][:6] == [None] * 6 and grid[0][6] == date(2026, 11, 1)
    assert shift_month(2026, 12, 1) == (2027, 1)
    assert shift_month(2026, 1, -1) == (2025, 12)


# ---------- booking service ----------

def test_booking_blocks_overlapping_slot(service):
    start = datetime(2026, 11, 9, 10, 0)
    assert service.book(1, "combo", start) is not None  # 10:00–10:50
    assert service.book(2, "cut", datetime(2026, 11, 9, 10, 30)) is None
    assert datetime(2026, 11, 9, 10, 30) not in service.slots(MONDAY, "cut")
    assert datetime(2026, 11, 9, 11, 0) in service.slots(MONDAY, "cut")


def test_sunday_and_closed_days_are_not_bookable(service):
    assert service.slots(date(2026, 11, 8), "cut") == []  # Sunday
    service.db.toggle_closed(MONDAY)
    assert service.slots(MONDAY, "cut") == []
    service.db.toggle_closed(MONDAY)
    assert service.slots(MONDAY, "cut")


def test_reschedule_moves_booking(service):
    booking_id = service.book(1, "cut", datetime(2026, 11, 9, 10, 0))
    assert service.move(booking_id, datetime(2026, 11, 9, 15, 0))
    assert service.db.get_booking(booking_id).start == datetime(2026, 11, 9, 15, 0)
    assert datetime(2026, 11, 9, 10, 0) in service.slots(MONDAY, "cut")


def test_cancel_frees_slot(service):
    start = datetime(2026, 11, 9, 10, 0)
    booking_id = service.book(1, "cut", start)
    service.db.cancel(booking_id)
    assert start in service.slots(MONDAY, "cut")
    assert service.db.upcoming_for_user(1, NOW) == []


def test_reminders_are_sent_once(service):
    booking_id = service.book(1, "cut", datetime(2026, 11, 9, 10, 0))
    day_before = datetime(2026, 11, 8, 11, 0)
    assert [b.id for b in service.db.due_reminders(day_before, "24h")] == [booking_id]
    service.db.mark_reminded(booking_id, "24h")
    assert service.db.due_reminders(day_before, "24h") == []

    hour_before = datetime(2026, 11, 9, 9, 15)
    assert [b.id for b in service.db.due_reminders(hour_before, "1h")] == [booking_id]


def test_short_notice_booking_skips_24h_reminder(service):
    service.book(1, "cut", datetime(2026, 11, 7, 10, 0))  # less than 24h ahead of NOW
    assert service.db.due_reminders(datetime(2026, 11, 6, 12, 30), "24h") == []

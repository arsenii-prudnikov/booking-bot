"""SQLite storage for users, bookings and closed days."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Iterator

FMT = "%Y-%m-%d %H:%M"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id         INTEGER PRIMARY KEY,
    name       TEXT NOT NULL DEFAULT '',
    lang       TEXT
);
CREATE TABLE IF NOT EXISTS bookings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    service      TEXT NOT NULL,
    start        TEXT NOT NULL,
    end          TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'active',  -- active | cancelled
    confirmed    INTEGER NOT NULL DEFAULT 0,      -- customer pressed "I'll be there"
    reminded_24h INTEGER NOT NULL DEFAULT 0,
    reminded_1h  INTEGER NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_bookings_start ON bookings(start);
CREATE TABLE IF NOT EXISTS closed_days (
    day TEXT PRIMARY KEY
);
"""


@dataclass(frozen=True)
class Booking:
    id: int
    user_id: int
    service: str
    start: datetime
    end: datetime
    status: str
    confirmed: bool
    user_name: str = ""
    user_lang: str | None = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Booking":
        keys = row.keys()
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            service=row["service"],
            start=datetime.strptime(row["start"], FMT),
            end=datetime.strptime(row["end"], FMT),
            status=row["status"],
            confirmed=bool(row["confirmed"]),
            user_name=row["name"] if "name" in keys and row["name"] else "",
            user_lang=row["lang"] if "lang" in keys else None,
        )


SELECT_BOOKING = """
SELECT b.*, u.name, u.lang FROM bookings b
LEFT JOIN users u ON u.id = b.user_id
"""


class Database:
    def __init__(self, path: str = "bookings.db") -> None:
        self.path = path
        with self._connect() as conn:
            self._migrate_v1(conn)
            conn.executescript(SCHEMA)

    @staticmethod
    def _migrate_v1(conn: sqlite3.Connection) -> None:
        """Version 1 stored bookings as (day, time). Keep that table aside and start fresh."""
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(bookings)")}
        if columns and "start" not in columns:
            conn.execute("DROP TABLE IF EXISTS bookings_v1")
            conn.execute("ALTER TABLE bookings RENAME TO bookings_v1")

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, isolation_level=None)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    # ---------- users ----------

    def save_user(self, user_id: int, name: str, lang: str | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO users (id, name, lang) VALUES (?, ?, ?) "
                "ON CONFLICT(id) DO UPDATE SET name = excluded.name, "
                "lang = COALESCE(excluded.lang, users.lang)",
                (user_id, name, lang),
            )

    def get_lang(self, user_id: int) -> str | None:
        with self._connect() as conn:
            row = conn.execute("SELECT lang FROM users WHERE id = ?", (user_id,)).fetchone()
        return row["lang"] if row else None

    # ---------- bookings ----------

    def busy_on(self, day: date, exclude_id: int | None = None) -> list[tuple[datetime, datetime]]:
        with self._connect() as conn:
            return self._busy_on(conn, day, exclude_id)

    @staticmethod
    def _busy_on(conn, day: date, exclude_id: int | None) -> list[tuple[datetime, datetime]]:
        rows = conn.execute(
            "SELECT start, end FROM bookings WHERE status = 'active' "
            "AND start >= ? AND start < ? AND id != ?",
            (day.isoformat(), (day + timedelta(days=1)).isoformat(), exclude_id or -1),
        ).fetchall()
        return [(datetime.strptime(r["start"], FMT), datetime.strptime(r["end"], FMT)) for r in rows]

    def _has_conflict(self, conn, start: datetime, end: datetime, exclude_id: int | None) -> bool:
        return any(
            start < b_end and b_start < end
            for b_start, b_end in self._busy_on(conn, start.date(), exclude_id)
        )

    def create_booking(
        self, user_id: int, service: str, start: datetime, end: datetime, now: datetime
    ) -> int | None:
        """Insert a booking; returns its id, or None if the slot was taken meanwhile."""
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")  # lock so two customers can't take the same slot
            if self._has_conflict(conn, start, end, None):
                conn.execute("ROLLBACK")
                return None
            lead = start - now
            cur = conn.execute(
                "INSERT INTO bookings (user_id, service, start, end, reminded_24h, reminded_1h, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id, service, start.strftime(FMT), end.strftime(FMT),
                    int(lead <= timedelta(hours=24)), int(lead <= timedelta(hours=1)),
                    now.strftime(FMT),
                ),
            )
            conn.execute("COMMIT")
            return cur.lastrowid

    def reschedule(self, booking_id: int, start: datetime, end: datetime, now: datetime) -> bool:
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            if self._has_conflict(conn, start, end, booking_id):
                conn.execute("ROLLBACK")
                return False
            lead = start - now
            conn.execute(
                "UPDATE bookings SET start = ?, end = ?, confirmed = 0, "
                "reminded_24h = ?, reminded_1h = ? WHERE id = ?",
                (
                    start.strftime(FMT), end.strftime(FMT),
                    int(lead <= timedelta(hours=24)), int(lead <= timedelta(hours=1)),
                    booking_id,
                ),
            )
            conn.execute("COMMIT")
            return True

    def get_booking(self, booking_id: int) -> Booking | None:
        with self._connect() as conn:
            row = conn.execute(SELECT_BOOKING + "WHERE b.id = ?", (booking_id,)).fetchone()
        return Booking.from_row(row) if row else None

    def upcoming_for_user(self, user_id: int, now: datetime) -> list[Booking]:
        with self._connect() as conn:
            rows = conn.execute(
                SELECT_BOOKING + "WHERE b.user_id = ? AND b.status = 'active' AND b.start >= ? "
                "ORDER BY b.start",
                (user_id, now.strftime(FMT)),
            ).fetchall()
        return [Booking.from_row(r) for r in rows]

    def bookings_between(self, start: datetime, end: datetime, status: str = "active") -> list[Booking]:
        with self._connect() as conn:
            rows = conn.execute(
                SELECT_BOOKING + "WHERE b.status = ? AND b.start >= ? AND b.start < ? ORDER BY b.start",
                (status, start.strftime(FMT), end.strftime(FMT)),
            ).fetchall()
        return [Booking.from_row(r) for r in rows]

    def cancel(self, booking_id: int) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))

    def confirm(self, booking_id: int) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE bookings SET confirmed = 1 WHERE id = ?", (booking_id,))

    # ---------- reminders ----------

    def due_reminders(self, now: datetime, kind: str) -> list[Booking]:
        """Bookings that need the 24h or 1h reminder right now."""
        column, window_start, window_end = {
            "24h": ("reminded_24h", now + timedelta(hours=1), now + timedelta(hours=24)),
            "1h": ("reminded_1h", now, now + timedelta(hours=1)),
        }[kind]
        with self._connect() as conn:
            rows = conn.execute(
                SELECT_BOOKING + f"WHERE b.status = 'active' AND b.{column} = 0 "
                "AND b.start > ? AND b.start <= ?",
                (window_start.strftime(FMT), window_end.strftime(FMT)),
            ).fetchall()
        return [Booking.from_row(r) for r in rows]

    def mark_reminded(self, booking_id: int, kind: str) -> None:
        column = {"24h": "reminded_24h", "1h": "reminded_1h"}[kind]
        with self._connect() as conn:
            conn.execute(f"UPDATE bookings SET {column} = 1 WHERE id = ?", (booking_id,))

    # ---------- closed days ----------

    def is_closed(self, day: date) -> bool:
        with self._connect() as conn:
            return conn.execute("SELECT 1 FROM closed_days WHERE day = ?", (day.isoformat(),)).fetchone() is not None

    def toggle_closed(self, day: date) -> bool:
        """Close an open day or reopen a closed one. Returns True if now closed."""
        with self._connect() as conn:
            if conn.execute("DELETE FROM closed_days WHERE day = ?", (day.isoformat(),)).rowcount:
                return False
            conn.execute("INSERT INTO closed_days (day) VALUES (?)", (day.isoformat(),))
            return True

    def closed_days(self) -> set[date]:
        with self._connect() as conn:
            return {date.fromisoformat(r["day"]) for r in conn.execute("SELECT day FROM closed_days")}

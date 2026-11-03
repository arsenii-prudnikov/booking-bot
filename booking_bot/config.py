"""Business settings: services, opening hours and environment configuration.

Everything a salon owner would want to change lives in this file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class Service:
    id: str
    emoji: str
    duration_min: int
    price_eur: int


SERVICES: dict[str, Service] = {
    s.id: s
    for s in (
        Service("cut", "✂️", 30, 25),
        Service("beard", "🧔", 20, 15),
        Service("combo", "💈", 50, 35),
    )
}

# Weekday (0 = Monday) -> (open, close). Missing days are closed.
OPENING_HOURS: dict[int, tuple[time, time]] = {
    0: (time(9, 0), time(18, 0)),
    1: (time(9, 0), time(18, 0)),
    2: (time(9, 0), time(18, 0)),
    3: (time(9, 0), time(18, 0)),
    4: (time(9, 0), time(18, 0)),
    5: (time(10, 0), time(15, 0)),
}

SLOT_STEP_MIN = 30  # a new appointment can start every 30 minutes
MIN_LEAD_MIN = 60  # earliest booking is one hour from now
BOOKING_HORIZON_DAYS = 30  # how far ahead customers can book


def _parse_ids(raw: str) -> frozenset[int]:
    return frozenset(int(x) for x in raw.replace(" ", "").split(",") if x)


@dataclass(frozen=True)
class Settings:
    token: str
    owner_chat_id: int | None
    admin_ids: frozenset[int] = field(default_factory=frozenset)
    business_name: str = "Barber Demo Kassel"
    address: str = "Musterstraße 1, 34117 Kassel"
    db_path: str = "bookings.db"
    tz: ZoneInfo = ZoneInfo("Europe/Berlin")

    @classmethod
    def from_env(cls) -> "Settings":
        owner = os.environ.get("OWNER_ID", "").strip()
        owner_id = int(owner) if owner else None
        admins = _parse_ids(os.environ.get("ADMIN_IDS", ""))
        if owner_id is not None and owner_id > 0:
            # A positive OWNER_ID is a person, so they are an admin too.
            admins |= {owner_id}
        return cls(
            token=os.environ["BOT_TOKEN"],
            owner_chat_id=owner_id,
            admin_ids=admins,
            business_name=os.environ.get("BUSINESS_NAME", cls.business_name),
            address=os.environ.get("BUSINESS_ADDRESS", cls.address),
            db_path=os.environ.get("DB_PATH", cls.db_path),
            tz=ZoneInfo(os.environ.get("TIMEZONE", "Europe/Berlin")),
        )

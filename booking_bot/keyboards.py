"""Inline keyboards. Callback data stays short because Telegram allows only 64 bytes."""

from __future__ import annotations

from datetime import date, datetime

from telegram import InlineKeyboardButton as Btn
from telegram import InlineKeyboardMarkup as Markup

from . import config
from .db import Booking
from .i18n import LANGS, WEEKDAYS, fmt_day, month_title, t
from .scheduling import month_grid, shift_month

NOOP = "noop"


def service_name(lang: str | None, service_id: str) -> str:
    return t(lang, f"svc_{service_id}")


def language_menu() -> Markup:
    return Markup([[Btn(label, callback_data=f"lang:{code}")] for code, label in LANGS.items()])


def main_menu(lang: str | None) -> Markup:
    return Markup([
        [Btn(t(lang, "btn_book"), callback_data="book")],
        [Btn(t(lang, "btn_my"), callback_data="my")],
        [Btn(t(lang, "btn_info"), callback_data="info"), Btn(t(lang, "btn_lang"), callback_data="langmenu")],
    ])


def back_to_menu(lang: str | None) -> Markup:
    return Markup([[Btn(t(lang, "btn_menu"), callback_data="menu")]])


def services_menu(lang: str | None, reschedule_id: int = 0) -> Markup:
    rows = []
    for s in config.SERVICES.values():
        label = t(lang, "service_line", emoji=s.emoji, name=service_name(lang, s.id),
                  duration=s.duration_min, price=s.price_eur)
        rows.append([Btn(label, callback_data=f"cal:{s.id}:{reschedule_id}")])
    rows.append([Btn(t(lang, "btn_back"), callback_data="menu")])
    return Markup(rows)


def calendar(
    lang: str | None,
    year: int,
    month: int,
    available: set[date],
    first: date,
    last: date,
    day_callback: str,
    nav_callback: str,
    back_callback: str,
    closed: set[date] | None = None,
) -> Markup:
    """Month view. Available days get a ✨, everything else is a dot.

    `day_callback` and `nav_callback` are templates with {day} / {ym} placeholders.
    When `closed` is given (owner view) every day in range is clickable.
    """
    rows = [[Btn(f"🗓 {month_title(lang, year, month)}", callback_data=NOOP)]]
    rows.append([Btn(w, callback_data=NOOP) for w in WEEKDAYS.get(lang or "de", WEEKDAYS["de"])])

    for week in month_grid(year, month):
        row = []
        for d in week:
            if d is None or not first <= d <= last:
                row.append(Btn(" " if d is None else "·", callback_data=NOOP))
            elif closed is not None:
                label = f"❌{d.day}" if d in closed else str(d.day)
                row.append(Btn(label, callback_data=day_callback.format(day=d.strftime("%Y%m%d"))))
            elif d in available:
                row.append(Btn(f"{d.day}✨", callback_data=day_callback.format(day=d.strftime("%Y%m%d"))))
            else:
                row.append(Btn("·", callback_data=NOOP))
        rows.append(row)

    prev_y, prev_m = shift_month(year, month, -1)
    next_y, next_m = shift_month(year, month, +1)
    nav = []
    if (prev_y, prev_m) >= (first.year, first.month):
        nav.append(Btn("◀️", callback_data=nav_callback.format(ym=f"{prev_y}{prev_m:02d}")))
    if (next_y, next_m) <= (last.year, last.month):
        nav.append(Btn("▶️", callback_data=nav_callback.format(ym=f"{next_y}{next_m:02d}")))
    if nav:
        rows.append(nav)
    rows.append([Btn(t(lang, "btn_back"), callback_data=back_callback)])
    return Markup(rows)


def time_slots(lang: str | None, service_id: str, slots: list[datetime], reschedule_id: int) -> Markup:
    buttons = [
        Btn(f"🕐 {s:%H:%M}", callback_data=f"slot:{service_id}:{s:%Y%m%d%H%M}:{reschedule_id}")
        for s in slots
    ]
    rows = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
    rows.append([Btn(t(lang, "btn_back"), callback_data=f"cal:{service_id}:{reschedule_id}")])
    return Markup(rows)


def confirm_booking(lang: str | None, service_id: str, start: datetime, reschedule_id: int) -> Markup:
    return Markup([
        [Btn(t(lang, "btn_confirm"), callback_data=f"ok:{service_id}:{start:%Y%m%d%H%M}:{reschedule_id}")],
        [Btn(t(lang, "btn_back"), callback_data=f"day:{service_id}:{start:%Y%m%d}:{reschedule_id}"),
         Btn(t(lang, "btn_cancel_flow"), callback_data="menu")],
    ])


def my_bookings(lang: str | None, bookings: list[Booking]) -> Markup:
    rows = [
        [Btn(f"{config.SERVICES[b.service].emoji} {fmt_day(lang, b.start)} · {b.start:%H:%M}",
             callback_data=f"bk:{b.id}")]
        for b in bookings
    ]
    rows.append([Btn(t(lang, "btn_menu"), callback_data="menu")])
    return Markup(rows)


def booking_actions(lang: str | None, booking: Booking, with_coming: bool = False, back: bool = True) -> Markup:
    rows = []
    if with_coming:
        rows.append([Btn(t(lang, "btn_coming"), callback_data=f"come:{booking.id}")])
    rows.append([
        Btn(t(lang, "btn_reschedule"), callback_data=f"cal:{booking.service}:{booking.id}"),
        Btn(t(lang, "btn_cancel_booking"), callback_data=f"cx:{booking.id}"),
    ])
    if back:
        rows.append([Btn(t(lang, "btn_back"), callback_data="my")])
    return Markup(rows)


def ask_cancel(lang: str | None, booking_id: int) -> Markup:
    return Markup([[
        Btn(t(lang, "btn_yes_cancel"), callback_data=f"cxy:{booking_id}"),
        Btn(t(lang, "btn_no"), callback_data=f"bk:{booking_id}"),
    ]])

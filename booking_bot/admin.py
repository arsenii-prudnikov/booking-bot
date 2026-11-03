"""Owner panel: today's appointments, weekly statistics, closing days."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton as Btn
from telegram import InlineKeyboardMarkup as Markup
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from . import config
from . import keyboards as kb
from .handlers import edit, svc
from .i18n import ADMIN_TEXTS as A
from .i18n import fmt_day, t

LANG = "de"


def is_admin(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    return user_id in svc(context).settings.admin_ids


def panel_markup() -> Markup:
    return Markup([
        [Btn(A["btn_today"], callback_data="adm:today")],
        [Btn(A["btn_week"], callback_data="adm:stats")],
        [Btn(A["btn_close_day"], callback_data="adm:cal")],
    ])


def back() -> Markup:
    return Markup([[Btn("◀️ Zurück", callback_data="adm:panel")]])


def panel_text(context) -> str:
    service = svc(context)
    now = service.now()
    day_start = now.replace(hour=0, minute=0)
    today = len(service.db.bookings_between(day_start, day_start + timedelta(days=1)))
    week = len(service.db.bookings_between(day_start, day_start + timedelta(days=7)))
    return A["panel"].format(today=today, week=week)


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_admin(context, update.effective_user.id):
        await update.message.reply_text("⛔️ " + t(LANG, "admin_only"))
        return
    await update.message.reply_text(panel_text(context), reply_markup=panel_markup(), parse_mode=ParseMode.HTML)


async def r_admin(update, context, lang, rest):
    query = update.callback_query
    if not is_admin(context, query.from_user.id):
        await query.answer("⛔️", show_alert=True)
        return
    await query.answer()
    action, _, arg = rest.partition(":")
    service = svc(context)
    now = service.now()
    today = now.date()

    if action == "panel":
        await edit(update, panel_text(context), panel_markup())

    elif action == "today":
        start = datetime.combine(today, datetime.min.time())
        bookings = service.db.bookings_between(start, start + timedelta(days=1))
        if not bookings:
            await edit(update, A["today_empty"], back())
            return
        lines = "\n".join(
            f"{'✅' if b.confirmed else '🕐'} <b>{b.start:%H:%M}</b> – {b.end:%H:%M} · "
            f"{config.SERVICES[b.service].emoji} {kb.service_name(LANG, b.service)} · {b.user_name or '–'}"
            for b in bookings
        )
        await edit(update, A["today"].format(day=fmt_day(LANG, today), lines=lines), back())

    elif action == "stats":
        week_ago = now - timedelta(days=7)
        done = service.db.bookings_between(week_ago, now)
        cancelled = service.db.bookings_between(week_ago, now, status="cancelled")
        upcoming = service.db.bookings_between(now, now + timedelta(days=7))
        revenue = sum(config.SERVICES[b.service].price_eur for b in done)
        top = Counter(b.service for b in done).most_common(1)
        top_name = f"{config.SERVICES[top[0][0]].emoji} {kb.service_name(LANG, top[0][0])}" if top else "–"
        await edit(update, A["stats"].format(
            count=len(done), cancelled=len(cancelled), revenue=revenue, top=top_name, upcoming=len(upcoming)
        ), back())

    elif action in ("cal", "toggle"):
        year, month = today.year, today.month
        if action == "toggle":
            day = datetime.strptime(arg, "%Y%m%d").date()
            service.db.toggle_closed(day)
            year, month = day.year, day.month
        elif arg:
            year, month = int(arg[:4]), int(arg[4:])
        first, last = service.bookable_range()
        markup = kb.calendar(
            LANG, year, month, available=set(), first=first, last=last,
            day_callback="adm:toggle:{day}", nav_callback="adm:cal:{ym}",
            back_callback="adm:panel", closed=service.db.closed_days(),
        )
        await edit(update, A["close_day"], markup)

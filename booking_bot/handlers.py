"""Customer-facing handlers: language, booking, my appointments, reminders."""

from __future__ import annotations

import logging
from datetime import datetime

from telegram import Update
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden
from telegram.ext import ContextTypes

from . import config
from . import keyboards as kb
from .booking import BookingService
from .db import Booking
from .i18n import ADMIN_TEXTS, fmt_day, t

log = logging.getLogger(__name__)
HTML = ParseMode.HTML


def svc(context: ContextTypes.DEFAULT_TYPE) -> BookingService:
    return context.application.bot_data["service"]


def user_lang(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> str | None:
    return svc(context).db.get_lang(user_id)


def booking_fields(lang: str | None, b: Booking) -> dict:
    s = config.SERVICES[b.service]
    return {
        "emoji": s.emoji,
        "service": kb.service_name(lang, b.service),
        "day": fmt_day(lang, b.start),
        "time": f"{b.start:%H:%M}",
        "price": s.price_eur,
    }


async def notify_owner(context: ContextTypes.DEFAULT_TYPE, key: str, b: Booking) -> None:
    chat_id = svc(context).settings.owner_chat_id
    if chat_id is None:
        return
    fields = booking_fields("de", b)
    try:
        await context.bot.send_message(
            chat_id, ADMIN_TEXTS[key].format(name=b.user_name or "–", **fields), parse_mode=HTML
        )
    except (BadRequest, Forbidden) as exc:
        log.warning("Could not notify owner: %s", exc)


async def edit(update: Update, text: str, markup=None) -> None:
    try:
        await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=HTML)
    except BadRequest as exc:  # pressing the same button twice
        if "not modified" not in str(exc):
            raise


# ---------- commands ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    log.info("/start from %s (%s)", user.full_name, user.id)
    service = svc(context)
    service.db.save_user(user.id, user.full_name)
    lang = service.db.get_lang(user.id)
    if lang is None:
        await update.message.reply_text(t("de", "choose_lang"), reply_markup=kb.language_menu())
        return
    await send_welcome(update.effective_chat.id, lang, context)


async def send_welcome(chat_id: int, lang: str, context: ContextTypes.DEFAULT_TYPE) -> None:
    # A message with a single emoji is shown by Telegram as a big animation.
    await context.bot.send_message(chat_id, "💈")
    await context.bot.send_message(
        chat_id,
        t(lang, "welcome", business=svc(context).settings.business_name) + "\n\n" + t(lang, "menu"),
        reply_markup=kb.main_menu(lang),
        parse_mode=HTML,
    )


# ---------- callback router ----------

async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data or ""
    user = query.from_user
    action, _, rest = data.partition(":")
    log.info("Button %s from %s", data, user.id)

    if action == "noop":
        await query.answer()
        return

    handler = ROUTES.get(action)
    if handler is None:
        await query.answer()
        return
    lang = user_lang(context, user.id)
    await handler(update, context, lang, rest)


async def r_lang(update, context, lang, rest):
    code = rest
    user = update.callback_query.from_user
    svc(context).db.save_user(user.id, user.full_name, code)
    await update.callback_query.answer("✅")
    try:
        await update.callback_query.delete_message()
    except BadRequest:  # messages older than 48 hours cannot be deleted
        pass
    await send_welcome(update.effective_chat.id, code, context)


async def r_lang_menu(update, context, lang, rest):
    await update.callback_query.answer()
    await edit(update, t(lang, "choose_lang"), kb.language_menu())


async def r_menu(update, context, lang, rest):
    await update.callback_query.answer()
    await edit(update, t(lang, "menu"), kb.main_menu(lang))


async def r_info(update, context, lang, rest):
    await update.callback_query.answer()
    settings = svc(context).settings
    services = "\n".join(
        t(lang, "service_line", emoji=s.emoji, name=kb.service_name(lang, s.id),
          duration=s.duration_min, price=s.price_eur)
        for s in config.SERVICES.values()
    )
    names = kb.WEEKDAYS.get(lang or "de", kb.WEEKDAYS["de"])
    hours = "\n".join(
        f"{names[d]}: " + (
            f"{config.OPENING_HOURS[d][0]:%H:%M}–{config.OPENING_HOURS[d][1]:%H:%M}"
            if d in config.OPENING_HOURS else t(lang, "closed")
        )
        for d in range(7)
    )
    text = t(lang, "info", business=settings.business_name, address=settings.address,
             services=services, hours=hours)
    await edit(update, text, kb.back_to_menu(lang))


async def r_book(update, context, lang, rest):
    await update.callback_query.answer()
    await edit(update, t(lang, "choose_service"), kb.services_menu(lang))


async def show_calendar(update, context, lang, service_id: str, year: int, month: int, rid: int):
    service = svc(context)
    first, last = service.bookable_range()
    month_days = [d for week in kb.month_grid(year, month) for d in week if d]
    available = service.available_days(month_days, service_id, exclude_id=rid or None)
    markup = kb.calendar(
        lang, year, month, available, first, last,
        day_callback=f"day:{service_id}:" + "{day}" + f":{rid}",
        nav_callback=f"calm:{service_id}:" + "{ym}" + f":{rid}",
        back_callback=f"bk:{rid}" if rid else "book",
    )
    await edit(update, t(lang, "choose_day", service=kb.service_name(lang, service_id)), markup)


async def r_calendar(update, context, lang, rest):
    service_id, rid = rest.split(":")
    await update.callback_query.answer()
    today = svc(context).now().date()
    await show_calendar(update, context, lang, service_id, today.year, today.month, int(rid))


async def r_calendar_month(update, context, lang, rest):
    service_id, ym, rid = rest.split(":")
    await update.callback_query.answer()
    await show_calendar(update, context, lang, service_id, int(ym[:4]), int(ym[4:]), int(rid))


async def r_day(update, context, lang, rest):
    service_id, ymd, rid = rest.split(":")
    day = datetime.strptime(ymd, "%Y%m%d").date()
    slots = svc(context).slots(day, service_id, exclude_id=int(rid) or None)
    if not slots:
        await update.callback_query.answer(t(lang, "day_full"), show_alert=True)
        return
    await update.callback_query.answer()
    await edit(
        update,
        t(lang, "choose_time", day=fmt_day(lang, day), service=kb.service_name(lang, service_id)),
        kb.time_slots(lang, service_id, slots, int(rid)),
    )


async def r_slot(update, context, lang, rest):
    service_id, stamp, rid = rest.split(":")
    start = datetime.strptime(stamp, "%Y%m%d%H%M")
    s = config.SERVICES[service_id]
    await update.callback_query.answer()
    text = t(lang, "confirm", emoji=s.emoji, service=kb.service_name(lang, service_id),
             day=fmt_day(lang, start), time=f"{start:%H:%M}", price=s.price_eur,
             address=svc(context).settings.address)
    await edit(update, text, kb.confirm_booking(lang, service_id, start, int(rid)))


async def r_confirm(update, context, lang, rest):
    service_id, stamp, rid = rest.split(":")
    rid = int(rid)
    start = datetime.strptime(stamp, "%Y%m%d%H%M")
    service = svc(context)
    user_id = update.callback_query.from_user.id

    if rid:
        booking = service.db.get_booking(rid)
        if booking is None or booking.user_id != user_id:
            await update.callback_query.answer(t(lang, "not_found"), show_alert=True)
            return
        ok, booking_id, key, owner_key = service.move(rid, start), rid, "rescheduled", "moved_booking"
    else:
        booking_id = service.book(user_id, service_id, start)
        ok, key, owner_key = booking_id is not None, "booked", "new_booking"

    if not ok:
        await update.callback_query.answer(t(lang, "slot_taken"), show_alert=True)
        await show_calendar(update, context, lang, service_id, start.year, start.month, rid)
        return

    await update.callback_query.answer("🎉")
    booking = service.db.get_booking(booking_id)
    await edit(update, t(lang, key, **booking_fields(lang, booking)), kb.back_to_menu(lang))
    await context.bot.send_message(update.effective_chat.id, "🎉")
    await notify_owner(context, owner_key, booking)


async def r_my(update, context, lang, rest):
    await update.callback_query.answer()
    service = svc(context)
    bookings = service.db.upcoming_for_user(update.callback_query.from_user.id, service.now())
    if not bookings:
        await edit(update, t(lang, "no_bookings"), kb.main_menu(lang))
        return
    await edit(update, t(lang, "my_bookings"), kb.my_bookings(lang, bookings))


def own_booking(context, update, booking_id: str) -> Booking | None:
    booking = svc(context).db.get_booking(int(booking_id))
    if booking and booking.user_id == update.callback_query.from_user.id and booking.status == "active":
        return booking
    return None


async def r_booking(update, context, lang, rest):
    if rest == "0":  # "back" from a fresh booking calendar
        await r_book(update, context, lang, rest)
        return
    booking = own_booking(context, update, rest)
    if booking is None:
        await update.callback_query.answer(t(lang, "not_found"), show_alert=True)
        return
    await update.callback_query.answer()
    await edit(update, t(lang, "booking_detail", **booking_fields(lang, booking)),
               kb.booking_actions(lang, booking))


async def r_ask_cancel(update, context, lang, rest):
    booking = own_booking(context, update, rest)
    if booking is None:
        await update.callback_query.answer(t(lang, "not_found"), show_alert=True)
        return
    await update.callback_query.answer()
    f = booking_fields(lang, booking)
    await edit(update, t(lang, "ask_cancel", service=f["service"], day=f["day"], time=f["time"]),
               kb.ask_cancel(lang, booking.id))


async def r_do_cancel(update, context, lang, rest):
    booking = own_booking(context, update, rest)
    if booking is None:
        await update.callback_query.answer(t(lang, "not_found"), show_alert=True)
        return
    svc(context).db.cancel(booking.id)
    await update.callback_query.answer()
    await edit(update, t(lang, "cancelled"), kb.main_menu(lang))
    await notify_owner(context, "cancelled_booking", booking)


async def r_coming(update, context, lang, rest):
    booking = own_booking(context, update, rest)
    if booking is None:
        await update.callback_query.answer(t(lang, "not_found"), show_alert=True)
        return
    svc(context).db.confirm(booking.id)
    await update.callback_query.answer(t(lang, "thanks_coming"))
    await update.callback_query.edit_message_reply_markup(None)


# ---------- reminders ----------

async def send_reminders(context: ContextTypes.DEFAULT_TYPE) -> None:
    service = svc(context)
    now = service.now()
    for kind in ("24h", "1h"):
        for b in service.db.due_reminders(now, kind):
            lang = b.user_lang
            text = t(lang, f"reminder_{kind}", address=service.settings.address, **booking_fields(lang, b))
            try:
                await context.bot.send_message(
                    b.user_id, text, parse_mode=HTML,
                    reply_markup=kb.booking_actions(lang, b, with_coming=True, back=False),
                )
            except Forbidden:
                log.info("User %s blocked the bot; skipping reminder", b.user_id)
            service.db.mark_reminded(b.id, kind)


ROUTES = {
    "lang": r_lang,
    "langmenu": r_lang_menu,
    "menu": r_menu,
    "info": r_info,
    "book": r_book,
    "cal": r_calendar,
    "calm": r_calendar_month,
    "day": r_day,
    "slot": r_slot,
    "ok": r_confirm,
    "my": r_my,
    "bk": r_booking,
    "cx": r_ask_cancel,
    "cxy": r_do_cancel,
    "come": r_coming,
}

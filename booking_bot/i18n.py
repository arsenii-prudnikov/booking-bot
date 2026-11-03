"""Texts in German, English and Russian."""

from __future__ import annotations

from datetime import date, datetime

LANGS = {"de": "🇩🇪 Deutsch", "en": "🇬🇧 English", "ru": "🇷🇺 Русский"}
DEFAULT_LANG = "de"

WEEKDAYS = {
    "de": ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"],
    "en": ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"],
    "ru": ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"],
}

MONTHS = {
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
           "August", "September", "Oktober", "November", "Dezember"],
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
    "ru": ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль",
           "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"],
}

TEXTS: dict[str, dict[str, str]] = {
    "de": {
        "choose_lang": "🌐 Bitte wählen Sie Ihre Sprache:",
        "welcome": "Willkommen bei <b>{business}</b>! 💈\n\nHier buchen Sie Ihren Termin in wenigen Sekunden – rund um die Uhr.",
        "menu": "Was möchten Sie tun?",
        "btn_book": "✂️ Termin buchen",
        "btn_my": "📅 Meine Termine",
        "btn_info": "ℹ️ Preise & Öffnungszeiten",
        "btn_lang": "🌐 Sprache",
        "btn_back": "◀️ Zurück",
        "btn_menu": "🏠 Menü",
        "choose_service": "Welche Leistung möchten Sie buchen?",
        "svc_cut": "Haarschnitt",
        "svc_beard": "Bart trimmen",
        "svc_combo": "Haarschnitt + Bart",
        "service_line": "{emoji} {name} · {duration} Min · {price} €",
        "choose_day": "📆 <b>{service}</b>\nWählen Sie einen Tag (✨ = freie Termine):",
        "choose_time": "🕐 <b>{day}</b>\nFreie Zeiten für {service}:",
        "day_full": "Dieser Tag ist leider ausgebucht. Bitte wählen Sie einen anderen.",
        "confirm": "Bitte prüfen Sie Ihren Termin:\n\n{emoji} <b>{service}</b>\n📅 {day}\n🕐 {time} Uhr\n💶 {price} €\n📍 {address}",
        "btn_confirm": "✅ Verbindlich buchen",
        "btn_cancel_flow": "❌ Abbrechen",
        "booked": "🎉 <b>Termin gebucht!</b>\n\n{emoji} {service}\n📅 {day} um {time} Uhr\n\nWir erinnern Sie 24 Stunden und 1 Stunde vorher.",
        "rescheduled": "🔁 <b>Termin verschoben!</b>\n\n{emoji} {service}\n📅 {day} um {time} Uhr",
        "slot_taken": "😕 Dieser Termin wurde gerade vergeben. Bitte wählen Sie eine andere Zeit.",
        "no_bookings": "Sie haben keine anstehenden Termine.",
        "my_bookings": "📅 <b>Ihre Termine</b>\nTippen Sie auf einen Termin, um ihn zu ändern:",
        "booking_detail": "{emoji} <b>{service}</b>\n📅 {day}\n🕐 {time} Uhr\n💶 {price} €",
        "btn_reschedule": "🔁 Verschieben",
        "btn_cancel_booking": "❌ Absagen",
        "ask_cancel": "Möchten Sie diesen Termin wirklich absagen?\n\n{service} · {day}, {time} Uhr",
        "btn_yes_cancel": "Ja, absagen",
        "btn_no": "Nein",
        "cancelled": "Ihr Termin wurde abgesagt. Wir hoffen, Sie bald wiederzusehen! 👋",
        "info": "💈 <b>{business}</b>\n📍 {address}\n\n<b>Preise</b>\n{services}\n\n<b>Öffnungszeiten</b>\n{hours}",
        "closed": "geschlossen",
        "reminder_24h": "⏰ <b>Erinnerung:</b> Morgen haben Sie einen Termin!\n\n{emoji} {service}\n📅 {day} um {time} Uhr\n📍 {address}",
        "reminder_1h": "⏰ <b>In einer Stunde</b> geht's los!\n\n{emoji} {service} um {time} Uhr\n📍 {address}",
        "btn_coming": "👍 Ich komme",
        "thanks_coming": "Super, bis gleich! 👍",
        "not_found": "Dieser Termin existiert nicht mehr.",
        "admin_only": "Dieser Bereich ist nur für den Inhaber.",
    },
    "en": {
        "choose_lang": "🌐 Please choose your language:",
        "welcome": "Welcome to <b>{business}</b>! 💈\n\nBook your appointment here in seconds – any time of day.",
        "menu": "What would you like to do?",
        "btn_book": "✂️ Book appointment",
        "btn_my": "📅 My appointments",
        "btn_info": "ℹ️ Prices & opening hours",
        "btn_lang": "🌐 Language",
        "btn_back": "◀️ Back",
        "btn_menu": "🏠 Menu",
        "choose_service": "Which service would you like to book?",
        "svc_cut": "Haircut",
        "svc_beard": "Beard trim",
        "svc_combo": "Haircut + beard",
        "service_line": "{emoji} {name} · {duration} min · €{price}",
        "choose_day": "📆 <b>{service}</b>\nChoose a day (✨ = free slots):",
        "choose_time": "🕐 <b>{day}</b>\nFree times for {service}:",
        "day_full": "Sorry, this day is fully booked. Please choose another one.",
        "confirm": "Please check your appointment:\n\n{emoji} <b>{service}</b>\n📅 {day}\n🕐 {time}\n💶 €{price}\n📍 {address}",
        "btn_confirm": "✅ Confirm booking",
        "btn_cancel_flow": "❌ Cancel",
        "booked": "🎉 <b>Appointment booked!</b>\n\n{emoji} {service}\n📅 {day} at {time}\n\nWe'll remind you 24 hours and 1 hour before.",
        "rescheduled": "🔁 <b>Appointment moved!</b>\n\n{emoji} {service}\n📅 {day} at {time}",
        "slot_taken": "😕 This time was just taken. Please choose another one.",
        "no_bookings": "You have no upcoming appointments.",
        "my_bookings": "📅 <b>Your appointments</b>\nTap one to change it:",
        "booking_detail": "{emoji} <b>{service}</b>\n📅 {day}\n🕐 {time}\n💶 €{price}",
        "btn_reschedule": "🔁 Reschedule",
        "btn_cancel_booking": "❌ Cancel",
        "ask_cancel": "Do you really want to cancel this appointment?\n\n{service} · {day}, {time}",
        "btn_yes_cancel": "Yes, cancel",
        "btn_no": "No",
        "cancelled": "Your appointment has been cancelled. Hope to see you soon! 👋",
        "info": "💈 <b>{business}</b>\n📍 {address}\n\n<b>Prices</b>\n{services}\n\n<b>Opening hours</b>\n{hours}",
        "closed": "closed",
        "reminder_24h": "⏰ <b>Reminder:</b> you have an appointment tomorrow!\n\n{emoji} {service}\n📅 {day} at {time}\n📍 {address}",
        "reminder_1h": "⏰ <b>See you in one hour!</b>\n\n{emoji} {service} at {time}\n📍 {address}",
        "btn_coming": "👍 I'll be there",
        "thanks_coming": "Great, see you soon! 👍",
        "not_found": "This appointment no longer exists.",
        "admin_only": "This section is for the owner only.",
    },
    "ru": {
        "choose_lang": "🌐 Выберите язык:",
        "welcome": "Добро пожаловать в <b>{business}</b>! 💈\n\nЗдесь можно записаться за пару секунд — в любое время.",
        "menu": "Что вы хотите сделать?",
        "btn_book": "✂️ Записаться",
        "btn_my": "📅 Мои записи",
        "btn_info": "ℹ️ Цены и часы работы",
        "btn_lang": "🌐 Язык",
        "btn_back": "◀️ Назад",
        "btn_menu": "🏠 Меню",
        "choose_service": "На какую услугу вы хотите записаться?",
        "svc_cut": "Стрижка",
        "svc_beard": "Оформление бороды",
        "svc_combo": "Стрижка + борода",
        "service_line": "{emoji} {name} · {duration} мин · {price} €",
        "choose_day": "📆 <b>{service}</b>\nВыберите день (✨ = есть свободное время):",
        "choose_time": "🕐 <b>{day}</b>\nСвободное время для услуги «{service}»:",
        "day_full": "К сожалению, этот день полностью занят. Выберите другой.",
        "confirm": "Проверьте запись:\n\n{emoji} <b>{service}</b>\n📅 {day}\n🕐 {time}\n💶 {price} €\n📍 {address}",
        "btn_confirm": "✅ Подтвердить запись",
        "btn_cancel_flow": "❌ Отмена",
        "booked": "🎉 <b>Вы записаны!</b>\n\n{emoji} {service}\n📅 {day} в {time}\n\nМы напомним за 24 часа и за 1 час.",
        "rescheduled": "🔁 <b>Запись перенесена!</b>\n\n{emoji} {service}\n📅 {day} в {time}",
        "slot_taken": "😕 Это время только что заняли. Выберите другое.",
        "no_bookings": "У вас нет предстоящих записей.",
        "my_bookings": "📅 <b>Ваши записи</b>\nНажмите на запись, чтобы изменить её:",
        "booking_detail": "{emoji} <b>{service}</b>\n📅 {day}\n🕐 {time}\n💶 {price} €",
        "btn_reschedule": "🔁 Перенести",
        "btn_cancel_booking": "❌ Отменить",
        "ask_cancel": "Точно отменить эту запись?\n\n{service} · {day}, {time}",
        "btn_yes_cancel": "Да, отменить",
        "btn_no": "Нет",
        "cancelled": "Запись отменена. Будем рады видеть вас снова! 👋",
        "info": "💈 <b>{business}</b>\n📍 {address}\n\n<b>Цены</b>\n{services}\n\n<b>Часы работы</b>\n{hours}",
        "closed": "выходной",
        "reminder_24h": "⏰ <b>Напоминание:</b> завтра у вас запись!\n\n{emoji} {service}\n📅 {day} в {time}\n📍 {address}",
        "reminder_1h": "⏰ <b>Через час</b> ждём вас!\n\n{emoji} {service} в {time}\n📍 {address}",
        "btn_coming": "👍 Я приду",
        "thanks_coming": "Отлично, до встречи! 👍",
        "not_found": "Этой записи больше нет.",
        "admin_only": "Этот раздел только для владельца.",
    },
}

# The owner panel is German only: the bot is built for a salon in Kassel.
ADMIN_TEXTS = {
    "panel": "🛠 <b>Inhaber-Panel</b>\n\nHeute: {today} Termine · Diese Woche: {week}",
    "btn_today": "📋 Termine heute",
    "btn_week": "📊 Statistik (7 Tage)",
    "btn_close_day": "🚫 Tage schließen/öffnen",
    "today_empty": "Heute sind keine Termine eingetragen. ☕",
    "today": "📋 <b>Termine heute, {day}</b>\n\n{lines}",
    "stats": (
        "📊 <b>Letzte 7 Tage</b>\n\n"
        "✅ Termine: {count}\n"
        "❌ Absagen: {cancelled}\n"
        "💶 Umsatz (geschätzt): {revenue} €\n"
        "🏆 Beliebteste Leistung: {top}\n\n"
        "📅 <b>Nächste 7 Tage</b>: {upcoming} Termine"
    ),
    "close_day": "🚫 Tippen Sie auf einen Tag, um ihn zu schließen oder wieder zu öffnen.\n❌ = geschlossen",
    "new_booking": "🆕 <b>Neue Buchung</b>\n👤 {name}\n{emoji} {service}\n📅 {day} um {time} Uhr",
    "moved_booking": "🔁 <b>Termin verschoben</b>\n👤 {name}\n{emoji} {service}\n📅 neu: {day} um {time} Uhr",
    "cancelled_booking": "❌ <b>Absage</b>\n👤 {name}\n{emoji} {service}\n📅 {day} um {time} Uhr",
}


def t(lang: str | None, key: str, **kwargs) -> str:
    texts = TEXTS.get(lang or DEFAULT_LANG, TEXTS[DEFAULT_LANG])
    return texts[key].format(**kwargs)


def fmt_day(lang: str | None, d: date | datetime) -> str:
    lang = lang if lang in WEEKDAYS else DEFAULT_LANG
    return f"{WEEKDAYS[lang][d.weekday()]}, {d.strftime('%d.%m.%Y')}"


def month_title(lang: str | None, year: int, month: int) -> str:
    lang = lang if lang in MONTHS else DEFAULT_LANG
    return f"{MONTHS[lang][month - 1]} {year}"

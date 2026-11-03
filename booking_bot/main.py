"""Entry point: wires settings, database, handlers and the reminder job together."""

from __future__ import annotations

import logging

from telegram import BotCommand, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

from . import admin, handlers
from .booking import BookingService
from .config import Settings
from .db import Database

log = logging.getLogger("booking_bot")


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.exception("Unhandled error", exc_info=context.error)


async def post_init(app: Application) -> None:
    await app.bot.set_my_commands([
        BotCommand("start", "Termin buchen / Book / Записаться"),
        BotCommand("admin", "Inhaber-Panel"),
    ])


def build_app(settings: Settings) -> Application:
    app = Application.builder().token(settings.token).post_init(post_init).build()
    app.bot_data["service"] = BookingService(Database(settings.db_path), settings)

    handlers.ROUTES["adm"] = admin.r_admin
    app.add_handler(CommandHandler("start", handlers.start))
    app.add_handler(CommandHandler("admin", admin.admin_command))
    app.add_handler(CallbackQueryHandler(handlers.on_button))
    app.add_error_handler(on_error)

    # Check once a minute for appointments that need a 24h or 1h reminder.
    app.job_queue.run_repeating(handlers.send_reminders, interval=60, first=10)
    return app


def main() -> None:
    logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    settings = Settings.from_env()
    log.info("Starting %s", settings.business_name)
    build_app(settings).run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

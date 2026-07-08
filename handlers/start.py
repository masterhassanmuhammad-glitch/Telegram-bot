from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from services import users_service

from ui.renderer import render_menu


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    users_service.register(update.effective_user)

    await render_menu(update, 0)


def register(application):
    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

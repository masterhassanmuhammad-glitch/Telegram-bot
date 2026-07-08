from telegram.ext import Application

from config import BOT_TOKEN

from handlers.start import register as register_start
from handlers.callback import register as register_callback


application = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)

register_start(application)
register_callback(application)

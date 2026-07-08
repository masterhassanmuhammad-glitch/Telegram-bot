from telegram.ext import Application

from config import BOT_TOKEN
from handlers.admin_menus import register as register_admin_menus

register_admin_menus(application)
from services.bootstrap_service import initialize

initialize()
from handlers.admin import register as register_admin

register_admin(application)
from handlers.start import register as register_start
from handlers.callback import register as register_callback
from handlers.admin_add_menu import register as register_admin_add_menu

register_admin_add_menu(application)

application = (
    Application.builder()
    .token(BOT_TOKEN)
    .build()
)

register_start(application)
register_callback(application)

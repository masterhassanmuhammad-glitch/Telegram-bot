import telebot
import logging
from flask import Flask, request

from config import API_TOKEN, PORT, RENDER_EXTERNAL_URL
from database import init_db, init_settings
from handlers import register_handlers

# ============================================
# LOGGING
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ============================================
# BOT INIT
# ============================================

bot = telebot.TeleBot(API_TOKEN, parse_mode="HTML")

# ============================================
# FLASK APP (FOR WEBHOOK)
# ============================================

app = Flask(__name__)

# ============================================
# INIT DATABASE
# ============================================

init_db()
init_settings(owner_id=8203001172)

# ============================================
# REGISTER HANDLERS
# ============================================

register_handlers(bot)

# ============================================
# WEBHOOK ROUTE
# ============================================

@app.route(f"/{API_TOKEN}", methods=["POST"])
def webhook():
    json_str = request.get_data().decode("utf-8")
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200


# ============================================
# SET WEBHOOK
# ============================================

def set_webhook():
    if RENDER_EXTERNAL_URL:
        url = f"{RENDER_EXTERNAL_URL}/{API_TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=url)
        logging.info(f"Webhook set to: {url}")
    else:
        logging.warning("RENDER_EXTERNAL_URL not set. Using polling.")


# ============================================
# START BOT
# ============================================

if __name__ == "__main__":

    set_webhook()

    if RENDER_EXTERNAL_URL:
        # Webhook mode (Render / production)
        logging.info("Starting Flask server (Webhook mode)")
        app.run(host="0.0.0.0", port=PORT)

    else:
        # Polling mode (local testing)
        logging.info("Starting bot (Polling mode)")
        bot.infinity_polling()

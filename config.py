import os

# ==========================================
# Telegram
# ==========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ==========================================
# Database
# ==========================================

DATABASE_URL = os.getenv("DATABASE_URL")

# ==========================================
# Render
# ==========================================

RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL")

PORT = int(os.getenv("PORT", 10000))

# ==========================================
# Debug
# ==========================================

DEBUG = os.getenv("DEBUG", "False").lower() == "true"

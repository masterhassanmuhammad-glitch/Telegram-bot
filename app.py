from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from telegram import Update

from config import BOT_TOKEN
from core.application import application


@asynccontextmanager
async def lifespan(app: FastAPI):
    await application.initialize()
    await application.start()
    yield
    await application.stop()
    await application.shutdown()


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def home():
    return {
        "status": "running",
        "engine": "BotEngine v2"
    }


@app.post("/")
async def telegram_webhook(request: Request):
    data = await request.json()

    update = Update.de_json(
        data,
        application.bot
    )

    await application.process_update(update)

    return {
        "ok": True
    }

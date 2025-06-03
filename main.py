import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import Update
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Базовая команда /start
@dp.message(commands=["start"])
async def cmd_start(message: types.Message):
    await message.answer("Привет! 👋 Это бот Avito × Дикая Мята.\n\nВыбери действие из меню.")

# Установка webhook
async def on_startup(app: web.Application):
    logging.info(">>> Устанавливаем webhook...")
    await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")

# Удаление webhook при остановке
async def on_shutdown(app: web.Application):
    logging.warning(">>> Удаляем webhook...")
    await bot.delete_webhook()

# AIOHTTP сервер
app = web.Application()
SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# Запуск
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

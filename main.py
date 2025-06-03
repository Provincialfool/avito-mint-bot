import os
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from dotenv import load_dotenv

# Загрузка .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = "/webhook"
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 10000))

# Инициализация бота и логгера
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer("Привет! 👋 Это бот Avito × Дикая Мята. Выбери действие из меню.")

@dp.message(F.photo)
async def handle_photo(message: Message):
    await message.answer("Спасибо за фото! 🎨 Стикер скоро будет доступен.")

@dp.message()
async def echo_text(message: Message):
    await message.answer("Я пока учусь отвечать. Напиши /start, чтобы начать заново.")

async def on_startup(app: web.Application):
    logging.info(">>> Устанавливаем webhook...")
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)

async def on_shutdown(app: web.Application):
    logging.info(">>> Удаляем webhook...")
    await bot.delete_webhook()

def main():
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    setup_application(app, dp, bot=bot)
    logging.info(f"Бот запущен на {HOST}:{PORT}")
    web.run_app(app, host=HOST, port=PORT)

if __name__ == "__main__":
    main()

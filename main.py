import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.webhook import WebhookUpdate
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message()
async def handle_message(message: types.Message):
    await message.answer("Привет! 👋 Это бот Avito × Дикая Мята. Выбери действие из меню.")

async def on_startup(app: web.Application):
    logging.info(">>> Устанавливаем webhook...")
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app: web.Application):
    logging.info(">>> Удаляем webhook...")
    await bot.delete_webhook()

async def webhook_handler(request: web.Request):
    data = await request.json()
    update = WebhookUpdate(**data)
    await dp.feed_update(bot=bot, update=update)
    return web.Response()

app = web.Application()
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)
app.router.add_post(WEBHOOK_PATH, webhook_handler)
setup_application(app, dp, bot=bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    web.run_app(app, host="0.0.0.0", port=10000)

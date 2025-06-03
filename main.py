import os
import logging
from aiohttp import web
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.types import Update
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart

# ────────────────────────────────────────────────────────────────
load_dotenv()                           # .env -> окружение
TOKEN        = os.getenv("BOT_TOKEN")
WEBHOOK_URL  = os.getenv("WEBHOOK_URL") # https://*.railway.app
WEBHOOK_PATH = "/webhook"               # фиксирован

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()

# ──────────────── Хендлеры ──────────────────────────────────────
@dp.message(CommandStart())
async def start_cmd(msg: types.Message):
    await msg.answer(
        "Привет! 👋 Это бот Avito × Дикая Мята.\n"
        "Пока умею отвечать на текст — меню добавим позже 😉"
    )

@dp.message(F.photo)
async def got_photo(msg: types.Message):
    await msg.answer("Фото получил, спасибо!")

@dp.message()
async def echo(msg: types.Message):
    await msg.answer("Ты написал: <code>{}</code>".format(msg.text))

# ──────────────── Webhook-сервер ────────────────────────────────
async def on_startup(_: web.Application):
    logging.info(">> Webhook set")
    await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")

async def on_shutdown(_: web.Application):
    logging.info(">> Webhook delete")
    await bot.delete_webhook()

async def handle(request: web.Request):
    data: dict = await request.json()
    update = Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return web.Response()

app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

# ──────────────── Запуск ────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    web.run_app(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

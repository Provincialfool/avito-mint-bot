
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiohttp import web
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")



bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Карта"), KeyboardButton(text="💃 Танцы")],
            [KeyboardButton(text="🧩 Квест"), KeyboardButton(text="🤳 Стикер")],
            [KeyboardButton(text="📅 Расписание"), KeyboardButton(text="🆘 Поддержка")],
            [KeyboardButton(text="🎥 Кружок")]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие"
    )

@dp.message(F.text == "/start")
async def start(message: Message):
    await message.answer(
        "Привет! 👋 Это бот Avito × Дикая Мята. Выбери действие из меню.",
        reply_markup=main_menu()
    )

@dp.message(F.text == "📍 Карта")
async def handle_map(message: Message):
    await message.answer("🗺 Здесь будет карта мероприятия.")

@dp.message(F.text == "💃 Танцы")
async def handle_dance(message: Message):
    await message.answer("💃 Пойдем танцевать!")

@dp.message(F.text == "🧩 Квест")
async def handle_quest(message: Message):
    await message.answer("🧩 Участвуй в квесте и выигрывай призы!")

@dp.message(F.text == "🤳 Стикер")
async def handle_sticker(message: Message):
    await message.answer("🤳 Получи стикер-пак по ссылке: https://t.me/addstickers/example")

@dp.message(F.text == "📅 Расписание")
async def handle_schedule(message: Message):
    await message.answer("📅 Смотри расписание здесь: https://example.com/schedule")

@dp.message(F.text == "🆘 Поддержка")
async def handle_support(message: Message):
    await message.answer("🆘 Напиши @support_helper по всем вопросам.")

@dp.message(F.text == "🎥 Кружок")
async def handle_circle(message: Message):
    video_path = "circle.mp4"
    if not os.path.exists(video_path):
        await message.answer("❌ Кружок не найден. Добавь файл circle.mp4 в корень проекта.")
        return
    video = FSInputFile(video_path)
    await bot.send_video_note(chat_id=message.chat.id, video_note=video)

async def webhook_handler(request):
    body = await request.read()
    update = bot.session.json_loads(body)
    await dp.feed_update(bot=bot, update=update)
    return web.Response()

async def on_startup(app):
    logger.info(">>> Устанавливаем webhook...")
    await bot.set_webhook(WEBHOOK_URL)

app = web.Application()
app.router.add_post("/webhook", webhook_handler)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=10000)

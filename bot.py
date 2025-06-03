import os
import logging
import json
import threading
from datetime import datetime
import telebot
from telebot import types
from app import app, db
from models import User, Registration, QuestProgress, StickerGeneration, AdminLog
from sticker_generator import generate_sticker
from quest_manager import QuestManager
import pandas as pd
import io

# Bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Initialize bot
bot = telebot.TeleBot(BOT_TOKEN)

# Initialize quest manager
quest_manager = QuestManager()

# Available time slots
TIME_SLOTS = ["12:00", "14:00", "16:00", "18:00", "20:00"]
DAYS = ["day1", "day2", "day3"]

# User states for photo upload
user_states = {}

@bot.message_handler(commands=['start'])
def start_command(message):
    """Handle /start command"""
    user_id = str(message.from_user.id)
    
    with app.app_context():
        # Create or get user
        db_user = User.query.filter_by(telegram_id=user_id).first()
        if not db_user:
            db_user = User(
                telegram_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name
            )
            db.session.add(db_user)
            db.session.commit()
    
    # Send welcome message
    welcome_text = f"🎪 Добро пожаловать на фестиваль Avito × Dikaya Myata, {message.from_user.first_name}!\n\n"
    welcome_text += "Выберите действие из меню ниже:"
    
    # Create inline keyboard
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📍 Карта", callback_data="map"))
    markup.row(
        types.InlineKeyboardButton("💃 Танцы", callback_data="dance"),
        types.InlineKeyboardButton("🧘 Йога", callback_data="yoga")
    )
    markup.row(
        types.InlineKeyboardButton("🧩 Квест", callback_data="quest"),
        types.InlineKeyboardButton("🤳 Стикер", callback_data="sticker")
    )
    markup.row(types.InlineKeyboardButton("📅 Расписание", callback_data="schedule"))
    
    bot.send_message(message.chat.id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    """Handle button callbacks"""
    user_id = str(call.from_user.id)
    data = call.data
    
    try:
        if data == "map":
            handle_map(call)
        elif data == "dance":
            handle_activity_registration(call, "dance")
        elif data == "yoga":
            handle_activity_registration(call, "yoga")
        elif data == "quest":
            handle_quest(call)
        elif data == "sticker":
            handle_sticker_request(call)
        elif data == "schedule":
            handle_schedule(call)
        elif data.startswith("register_"):
            handle_registration_selection(call)
        elif data == "back_to_menu":
            show_main_menu(call)
        
        bot.answer_callback_query(call.id)
    except Exception as e:
        logging.error(f"Error in callback handler: {e}")
        bot.answer_callback_query(call.id, "Произошла ошибка")

def handle_map(call):
    """Send festival map"""
    map_text = "🗺️ Карта фестиваля\n\n"
    map_text += "📍 Основные зоны:\n"
    map_text += "🎵 Главная сцена\n"
    map_text += "💃 Танцевальная площадка\n"
    map_text += "🧘 Йога-зона\n"
    map_text += "🍽️ Фуд-корт\n"
    map_text += "🏮 Маяк (для квеста)\n\n"
    map_text += "Нажмите на локацию на карте, чтобы узнать больше!"
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu"))
    
    bot.edit_message_text(map_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

def handle_activity_registration(call, activity_type):
    """Handle dance/yoga registration"""
    activity_name = "Танцы" if activity_type == "dance" else "Йога"
    
    text = f"💫 Регистрация на {activity_name}\n\n"
    text += "Выберите день и время:\n\n"
    
    markup = types.InlineKeyboardMarkup()
    for day_num, day in enumerate(DAYS, 1):
        day_name = f"День {day_num}"
        for time_slot in TIME_SLOTS:
            button_text = f"{day_name} - {time_slot}"
            callback_data = f"register_{activity_type}_{day}_{time_slot}"
            markup.row(types.InlineKeyboardButton(button_text, callback_data=callback_data))
    
    markup.row(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

def handle_registration_selection(call):
    """Handle specific registration selection"""
    data_parts = call.data.split("_")
    activity_type = data_parts[1]
    day = data_parts[2]
    time_slot = data_parts[3]
    
    user_id = str(call.from_user.id)
    
    with app.app_context():
        db_user = User.query.filter_by(telegram_id=user_id).first()
        if db_user:
            # Check if already registered for this slot
            existing = Registration.query.filter_by(
                user_id=db_user.id,
                activity_type=activity_type,
                day=day,
                time_slot=time_slot
            ).first()
            
            if existing:
                text = "❌ Вы уже зарегистрированы на это время!"
            else:
                registration = Registration(
                    user_id=db_user.id,
                    activity_type=activity_type,
                    day=day,
                    time_slot=time_slot
                )
                db.session.add(registration)
                db.session.commit()
                
                activity_name = "Танцы" if activity_type == "dance" else "Йога"
                day_num = day.replace("day", "")
                text = f"✅ Успешно зарегистрированы!\n\n"
                text += f"📅 {activity_name}\n"
                text += f"🗓️ День {day_num}\n"
                text += f"🕒 {time_slot}\n\n"
                text += "Увидимся на фестивале! 🎉"
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

def handle_quest(call):
    """Handle quest system"""
    user_id = str(call.from_user.id)
    
    with app.app_context():
        db_user = User.query.filter_by(telegram_id=user_id).first()
        if not db_user:
            return
        
        quest_progress = QuestProgress.query.filter_by(user_id=db_user.id).first()
        if not quest_progress:
            quest_progress = QuestProgress(user_id=db_user.id)
            db.session.add(quest_progress)
            db.session.commit()
        
        current_step = quest_progress.quest_step
        quest_info = quest_manager.get_quest_step(current_step)
        
        if quest_progress.completed:
            text = "🎉 Поздравляем! Вы успешно завершили квест!\n\n"
            text += "Покажите этот код организаторам для получения приза: QUEST_COMPLETE_2024"
        else:
            text = f"🧭 Квест - Шаг {current_step}\n\n"
            text += quest_info['description'] if quest_info else "Квест завершен"
        
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu"))
        
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

def handle_sticker_request(call):
    """Handle sticker generation request"""
    text = "🤳 Генерация персонального стикера\n\n"
    text += "Отправьте свое фото, и я создам для вас уникальный стикер с рамкой фестиваля!\n\n"
    text += "💡 Совет: Лучше всего работают фото с четким изображением лица на однотонном фоне."
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu"))
    
    # Set user state for photo upload
    user_states[call.from_user.id] = 'awaiting_photo'
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

def handle_schedule(call):
    """Show festival schedule"""
    text = "📅 Расписание фестиваля\n\n"
    text += "🎪 День 1\n"
    text += "12:00 - Открытие фестиваля\n"
    text += "14:00 - Танцы\n"
    text += "16:00 - Йога\n"
    text += "18:00 - Концерт\n"
    text += "20:00 - Вечеринка\n\n"
    
    text += "🎪 День 2\n"
    text += "12:00 - Мастер-классы\n"
    text += "14:00 - Танцы\n"
    text += "16:00 - Йога\n"
    text += "18:00 - Квест\n"
    text += "20:00 - Концерт\n\n"
    
    text += "🎪 День 3\n"
    text += "12:00 - Йога\n"
    text += "14:00 - Танцы\n"
    text += "16:00 - Финальное шоу\n"
    text += "18:00 - Закрытие фестиваля"
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_menu"))
    
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """Handle photo uploads for sticker generation"""
    if message.from_user.id not in user_states or user_states[message.from_user.id] != 'awaiting_photo':
        return
    
    user_id = str(message.from_user.id)
    
    bot.send_message(message.chat.id, "🔄 Обрабатываю ваше фото... Это может занять несколько секунд.")
    
    try:
        # Get the highest resolution photo
        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)
        photo_bytes = bot.download_file(file_info.file_path)
        
        with app.app_context():
            # Generate sticker (simplified version without external APIs for now)
            from sticker_generator import generate_simple_sticker, TEMPLATES
            import random
            
            template_info = random.choice(TEMPLATES)
            sticker_bytes = generate_simple_sticker(photo_bytes, template_info)
            
            if sticker_bytes:
                # Save to database
                db_user = User.query.filter_by(telegram_id=user_id).first()
                if db_user:
                    sticker_gen = StickerGeneration(
                        user_id=db_user.id,
                        template_used=template_info['name'],
                        original_photo_file_id=photo.file_id
                    )
                    db.session.add(sticker_gen)
                    db.session.commit()
                
                # Send sticker
                bot.send_photo(
                    message.chat.id,
                    sticker_bytes,
                    caption="🎉 Ваш персональный стикер готов!\n\n\"Хорошие истории начинаются с тебя\" ✨"
                )
            else:
                bot.send_message(message.chat.id, "❌ Не удалось обработать фото. Попробуйте другое изображение.")
    
    except Exception as e:
        logging.error(f"Error generating sticker: {e}")
        bot.send_message(message.chat.id, "❌ Произошла ошибка при обработке фото. Попробуйте позже.")
    
    finally:
        if message.from_user.id in user_states:
            del user_states[message.from_user.id]

def show_main_menu(call):
    """Show main menu"""
    welcome_text = "🎪 Главное меню фестиваля\n\nВыберите действие:"
    
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("📍 Карта", callback_data="map"))
    markup.row(
        types.InlineKeyboardButton("💃 Танцы", callback_data="dance"),
        types.InlineKeyboardButton("🧘 Йога", callback_data="yoga")
    )
    markup.row(
        types.InlineKeyboardButton("🧩 Квест", callback_data="quest"),
        types.InlineKeyboardButton("🤳 Стикер", callback_data="sticker")
    )
    markup.row(types.InlineKeyboardButton("📅 Расписание", callback_data="schedule"))
    
    bot.edit_message_text(welcome_text, call.message.chat.id, call.message.message_id, reply_markup=markup)

# Admin commands
@bot.message_handler(commands=['admin_log'])
def admin_log_command(message):
    """Export participant data as CSV"""
    user_id = str(message.from_user.id)
    
    with app.app_context():
        user = User.query.filter_by(telegram_id=user_id).first()
        if not user or not user.is_admin:
            bot.send_message(message.chat.id, "❌ У вас нет прав доступа к этой команде.")
            return
        
        # Get all registrations with user data
        registrations = db.session.query(Registration, User).join(User).all()
        
        data = []
        for reg, user in registrations:
            data.append({
                'telegram_id': user.telegram_id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'activity': reg.activity_type,
                'day': reg.day,
                'time_slot': reg.time_slot,
                'registered_at': reg.created_at
            })
        
        if data:
            df = pd.DataFrame(data)
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_bytes = csv_buffer.getvalue().encode('utf-8')
            
            filename = f"participants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            bot.send_document(message.chat.id, csv_bytes, visible_file_name=filename)
        else:
            bot.send_message(message.chat.id, "📊 Нет данных для экспорта.")

@bot.message_handler(commands=['reset'])
def reset_user_command(message):
    """Reset user data"""
    user_id = str(message.from_user.id)
    
    with app.app_context():
        admin_user = User.query.filter_by(telegram_id=user_id).first()
        if not admin_user or not admin_user.is_admin:
            bot.send_message(message.chat.id, "❌ У вас нет прав доступа к этой команде.")
            return
        
        command_parts = message.text.split()
        if len(command_parts) < 2:
            bot.send_message(message.chat.id, "Использование: /reset <telegram_id>")
            return
        
        target_telegram_id = command_parts[1]
        target_user = User.query.filter_by(telegram_id=target_telegram_id).first()
        
        if not target_user:
            bot.send_message(message.chat.id, "❌ Пользователь не найден.")
            return
        
        # Delete all user data
        Registration.query.filter_by(user_id=target_user.id).delete()
        QuestProgress.query.filter_by(user_id=target_user.id).delete()
        StickerGeneration.query.filter_by(user_id=target_user.id).delete()
        db.session.commit()
        
        bot.send_message(message.chat.id, f"✅ Данные пользователя {target_telegram_id} сброшены.")

@bot.message_handler(commands=['broadcast'])
def broadcast_command(message):
    """Broadcast message to all users"""
    user_id = str(message.from_user.id)
    
    with app.app_context():
        admin_user = User.query.filter_by(telegram_id=user_id).first()
        if not admin_user or not admin_user.is_admin:
            bot.send_message(message.chat.id, "❌ У вас нет прав доступа к этой команде.")
            return
        
        command_parts = message.text.split(maxsplit=1)
        if len(command_parts) < 2:
            bot.send_message(message.chat.id, "Использование: /broadcast <сообщение>")
            return
        
        broadcast_message = command_parts[1]
        users = User.query.all()
        
        sent_count = 0
        for user in users:
            try:
                bot.send_message(int(user.telegram_id), f"📢 {broadcast_message}")
                sent_count += 1
            except Exception as e:
                logging.error(f"Failed to send message to {user.telegram_id}: {e}")
        
        bot.send_message(message.chat.id, f"✅ Сообщение отправлено {sent_count} пользователям.")

def start_bot():
    """Start the Telegram bot"""
    logging.info("Starting Telegram bot...")
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logging.error(f"Bot polling error: {e}")

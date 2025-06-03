from app import db
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, Boolean

class User(db.Model):
    id = db.Column(Integer, primary_key=True)
    telegram_id = db.Column(String(20), unique=True, nullable=False)
    username = db.Column(String(100))
    first_name = db.Column(String(100))
    last_name = db.Column(String(100))
    created_at = db.Column(DateTime, default=datetime.utcnow)
    is_admin = db.Column(Boolean, default=False)
    
    # Relationships
    registrations = db.relationship('Registration', backref='user', lazy=True)
    quest_progress = db.relationship('QuestProgress', backref='user', lazy=True)
    stickers_generated = db.relationship('StickerGeneration', backref='user', lazy=True)

class Registration(db.Model):
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, db.ForeignKey('user.id'), nullable=False)
    activity_type = db.Column(String(50), nullable=False)  # 'dance' or 'yoga'
    time_slot = db.Column(String(10), nullable=False)  # '12:00', '14:00', etc.
    day = db.Column(String(20), nullable=False)  # 'day1', 'day2', 'day3'
    created_at = db.Column(DateTime, default=datetime.utcnow)

class QuestProgress(db.Model):
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, db.ForeignKey('user.id'), nullable=False)
    quest_step = db.Column(Integer, default=1)
    completed_steps = db.Column(Text)  # JSON string of completed steps
    photo_submissions = db.Column(Text)  # JSON string of photo file IDs
    completed = db.Column(Boolean, default=False)
    completed_at = db.Column(DateTime)
    created_at = db.Column(DateTime, default=datetime.utcnow)

class StickerGeneration(db.Model):
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(Integer, db.ForeignKey('user.id'), nullable=False)
    template_used = db.Column(String(50), nullable=False)
    original_photo_file_id = db.Column(String(200))
    generated_sticker_file_id = db.Column(String(200))
    created_at = db.Column(DateTime, default=datetime.utcnow)

class AdminLog(db.Model):
    id = db.Column(Integer, primary_key=True)
    action = db.Column(String(100), nullable=False)
    admin_telegram_id = db.Column(String(20), nullable=False)
    target_user_id = db.Column(Integer)
    details = db.Column(Text)
    created_at = db.Column(DateTime, default=datetime.utcnow)

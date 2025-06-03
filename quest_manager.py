import json
import logging
from datetime import datetime

class QuestManager:
    def __init__(self):
        self.quest_steps = {
            1: {
                "description": "🏮 Найдите маяк на территории фестиваля и отсканируйте QR-код, расположенный у его основания.",
                "requires_qr": True,
                "requires_photo": False,
                "next_step": 2
            },
            2: {
                "description": "📸 Отлично! Теперь сделайте селфи рядом с маяком и загрузите фото.",
                "requires_qr": False,
                "requires_photo": True,
                "next_step": 3
            },
            3: {
                "description": "🎵 Найдите главную сцену и сфотографируйте табличку с названиями выступающих артистов.",
                "requires_qr": False,
                "requires_photo": True,
                "next_step": 4
            },
            4: {
                "description": "🍽️ Посетите фуд-корт и найдите стенд с логотипом Avito. Сфотографируйте его.",
                "requires_qr": False,
                "requires_photo": True,
                "next_step": 5
            },
            5: {
                "description": "💃 Последнее задание! Найдите танцевальную площадку и отсканируйте финальный QR-код.",
                "requires_qr": True,
                "requires_photo": False,
                "next_step": "complete"
            }
        }
    
    def get_quest_step(self, step_number):
        """Get quest step information"""
        if step_number in self.quest_steps:
            return self.quest_steps[step_number]
        return None
    
    def validate_qr_code(self, qr_data, current_step):
        """Validate QR code for current step"""
        expected_codes = {
            1: "LIGHTHOUSE_QUEST_START",
            5: "DANCE_FLOOR_QUEST_END"
        }
        
        return qr_data == expected_codes.get(current_step, "")
    
    def process_photo_submission(self, user_id, step_number, photo_file_id):
        """Process photo submission for quest step"""
        # In a real implementation, this might involve:
        # - AI-powered image recognition to verify the photo content
        # - Manual review queue for admin approval
        # - Automatic approval for demo purposes
        
        valid_photo_steps = [2, 3, 4]
        
        if step_number in valid_photo_steps:
            logging.info(f"Photo submitted for user {user_id}, step {step_number}: {photo_file_id}")
            return True
        
        return False
    
    def advance_quest_step(self, quest_progress, action_type, data=None):
        """Advance user's quest progress"""
        from app import db
        from models import QuestProgress
        
        current_step = quest_progress.quest_step
        step_info = self.get_quest_step(current_step)
        
        if not step_info:
            return False, "Invalid quest step"
        
        # Validate action
        if action_type == "qr" and step_info["requires_qr"]:
            if not self.validate_qr_code(data, current_step):
                return False, "Invalid QR code"
        elif action_type == "photo" and step_info["requires_photo"]:
            if not self.process_photo_submission(quest_progress.user_id, current_step, data):
                return False, "Photo validation failed"
        else:
            return False, "Invalid action for this step"
        
        # Update progress
        completed_steps = json.loads(quest_progress.completed_steps or "[]")
        completed_steps.append({
            "step": current_step,
            "action": action_type,
            "data": data,
            "completed_at": datetime.utcnow().isoformat()
        })
        
        quest_progress.completed_steps = json.dumps(completed_steps)
        
        # Advance to next step
        if step_info["next_step"] == "complete":
            quest_progress.completed = True
            quest_progress.completed_at = datetime.utcnow()
            quest_progress.quest_step = current_step  # Keep at final step
        else:
            quest_progress.quest_step = step_info["next_step"]
        
        try:
            db.session.commit()
            return True, "Quest step completed successfully"
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating quest progress: {e}")
            return False, "Database error"
    
    def get_quest_summary(self, quest_progress):
        """Get summary of user's quest progress"""
        if not quest_progress:
            return {
                "current_step": 1,
                "total_steps": len(self.quest_steps),
                "completed_steps": 0,
                "is_completed": False,
                "completion_code": None
            }
        
        completed_steps = json.loads(quest_progress.completed_steps or "[]")
        
        summary = {
            "current_step": quest_progress.quest_step,
            "total_steps": len(self.quest_steps),
            "completed_steps": len(completed_steps),
            "is_completed": quest_progress.completed,
            "completion_code": "QUEST_COMPLETE_2024" if quest_progress.completed else None
        }
        
        return summary
    
    def get_leaderboard(self, limit=10):
        """Get quest completion leaderboard"""
        from models import QuestProgress, User
        from app import db
        
        # Get users who completed the quest, ordered by completion time
        completed_quests = db.session.query(QuestProgress, User).join(User).filter(
            QuestProgress.completed == True
        ).order_by(QuestProgress.completed_at.asc()).limit(limit).all()
        
        leaderboard = []
        for quest, user in completed_quests:
            leaderboard.append({
                "rank": len(leaderboard) + 1,
                "username": user.username or user.first_name,
                "completed_at": quest.completed_at,
                "total_time": None  # Could calculate from first step to completion
            })
        
        return leaderboard

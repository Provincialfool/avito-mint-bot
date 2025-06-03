from flask import render_template, request, redirect, url_for, flash, jsonify, send_file
from app import app, db
from models import User, Registration, QuestProgress, StickerGeneration, AdminLog
import pandas as pd
import io
from datetime import datetime

@app.route('/')
def index():
    """Admin dashboard"""
    with app.app_context():
        total_users = User.query.count()
        total_registrations = Registration.query.count()
        total_stickers = StickerGeneration.query.count()
        completed_quests = QuestProgress.query.filter_by(completed=True).count()
        
        # Recent activity
        recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
        recent_registrations = db.session.query(Registration, User).join(User).order_by(Registration.created_at.desc()).limit(10).all()
        
        return render_template('admin_dashboard.html',
                             total_users=total_users,
                             total_registrations=total_registrations,
                             total_stickers=total_stickers,
                             completed_quests=completed_quests,
                             recent_users=recent_users,
                             recent_registrations=recent_registrations)

@app.route('/participants')
def participants():
    """View all participants"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users = User.query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('participants.html', users=users)

@app.route('/export_csv')
def export_csv():
    """Export participants data as CSV"""
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
            'registered_at': reg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    if not data:
        flash('No data to export', 'warning')
        return redirect(url_for('index'))
    
    df = pd.DataFrame(data)
    
    # Create CSV in memory
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    
    # Convert to bytes
    csv_bytes = io.BytesIO()
    csv_bytes.write(output.getvalue().encode('utf-8'))
    csv_bytes.seek(0)
    
    filename = f"participants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )

@app.route('/broadcast', methods=['GET', 'POST'])
def broadcast():
    """Send broadcast message"""
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            # In a real implementation, this would queue the message for the bot to send
            flash(f'Broadcast message queued: {message}', 'success')
        else:
            flash('Message cannot be empty', 'error')
        
        return redirect(url_for('broadcast'))
    
    return render_template('broadcast.html')

@app.route('/api/stats')
def api_stats():
    """API endpoint for real-time stats"""
    stats = {
        'total_users': User.query.count(),
        'total_registrations': Registration.query.count(),
        'dance_registrations': Registration.query.filter_by(activity_type='dance').count(),
        'yoga_registrations': Registration.query.filter_by(activity_type='yoga').count(),
        'completed_quests': QuestProgress.query.filter_by(completed=True).count(),
        'generated_stickers': StickerGeneration.query.count()
    }
    return jsonify(stats)

@app.route('/user/<telegram_id>')
def user_detail(telegram_id):
    """View specific user details"""
    user = User.query.filter_by(telegram_id=telegram_id).first_or_404()
    
    registrations = Registration.query.filter_by(user_id=user.id).all()
    quest_progress = QuestProgress.query.filter_by(user_id=user.id).first()
    stickers = StickerGeneration.query.filter_by(user_id=user.id).all()
    
    return render_template('user_detail.html',
                         user=user,
                         registrations=registrations,
                         quest_progress=quest_progress,
                         stickers=stickers)

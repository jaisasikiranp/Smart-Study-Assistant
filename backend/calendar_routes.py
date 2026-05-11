from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify
from functools import wraps
from models import Task, db
from datetime import datetime

calendar_bp = Blueprint('calendar', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Support for desktop assistant via token
        from flask import request
        token = request.headers.get('X-Assistant-Token')
        if token == 'SMART-STUDY-2026':
            if 'user_id' not in session:
                session['user_id'] = 1
            return f(*args, **kwargs)

        if 'user_id' not in session:
            flash('Please log in to access your calendar.', 'error')
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@calendar_bp.route('/calendar')
@login_required
def calendar_view():
    return render_template('calendar.html')

@calendar_bp.route('/api/calendar_data')
@login_required
def get_calendar_data():
    user_id = session['user_id']
    tasks = Task.query.filter_by(user_id=user_id).all()
    
    calendar_tasks = []
    for t in tasks:
        if t.deadline:
            status_color = "#eab308" # Yellow (Upcoming)
            if t.status == 'completed':
                status_color = "#10b981" # Green
            elif t.deadline < datetime.now():
                status_color = "#ef4444" # Red (Overdue)
                
            calendar_tasks.append({
                "id": t.id,
                "title": t.title,
                "description": t.description,
                "deadline": t.deadline.strftime('%Y-%m-%d'),
                "time": t.deadline.strftime('%H:%M'),
                "status": t.status,
                "color": status_color
            })
    
    return jsonify(calendar_tasks)

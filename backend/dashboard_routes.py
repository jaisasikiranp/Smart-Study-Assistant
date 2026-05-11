from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify, request
from datetime import datetime, date, timedelta
from models import db, User, Task, Note, Resource
from functools import wraps

dashboard_bp = Blueprint('dashboard', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Support for desktop assistant via token
        token = request.headers.get('X-Assistant-Token')
        if token == 'SMART-STUDY-2026':
            if 'user_id' not in session:
                session['user_id'] = 1
            return f(*args, **kwargs)

        if 'user_id' not in session:
            flash('Please log in to access your dashboard.', 'error')
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@dashboard_bp.route('/dashboard')
@login_required
def dashboard_view():
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Summary Counts
    task_count = Task.query.filter_by(user_id=user_id, status='pending').count()
    note_count = Note.query.filter_by(user_id=user_id).count()
    resource_count = Resource.query.filter_by(user_id=user_id).count()

    return render_template('dashboard.html', 
                           user=user, 
                           task_count=task_count, 
                           note_count=note_count, 
                           resource_count=resource_count)

@dashboard_bp.route('/api/tasks/today')
@login_required
def get_today_tasks():
    user_id = session['user_id']
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())
    
    tasks = Task.query.filter(
        db.and_(Task.user_id == user_id, 
                Task.deadline >= today_start,
                Task.deadline <= today_end)
    ).order_by(Task.deadline.asc()).all()
    
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'status': t.status,
        'deadline': t.deadline.isoformat() if t.deadline else None
    } for t in tasks])

@dashboard_bp.route('/api/tasks/pending')
@login_required
def get_pending_tasks():
    user_id = session['user_id']
    tasks = Task.query.filter_by(user_id=user_id, status='pending').all()
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'deadline': t.deadline.isoformat() if t.deadline else None
    } for t in tasks])

@dashboard_bp.route('/api/tasks/upcoming')
@login_required
def get_upcoming_tasks():
    user_id = session['user_id']
    # Future deadlines (starting from tomorrow)
    tomorrow_start = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())
    
    tasks = Task.query.filter(
        db.and_(Task.user_id == user_id, 
                Task.deadline >= tomorrow_start, 
                Task.status == 'pending')
    ).order_by(Task.deadline.asc()).limit(5).all()
    
    return jsonify([{
        'id': t.id,
        'title': t.title,
        'deadline': t.deadline.strftime('%B %d, %Y') if t.deadline else "No deadline"
    } for t in tasks])

@dashboard_bp.route('/api/notes/all')
@login_required
def get_all_notes():
    user_id = session['user_id']
    notes = Note.query.filter_by(user_id=user_id).order_by(Note.title.asc()).all()
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'content': n.content[:100] + '...' if len(n.content) > 100 else n.content
    } for n in notes])

# API to add dummy data for testing
@dashboard_bp.route('/dashboard/seed')
@login_required
def seed_data():
    user_id = session['user_id']
    if Task.query.filter_by(user_id=user_id).first():
        return jsonify({"msg": "Already seeded"})

    t1 = Task(user_id=user_id, title="ML Assignment", deadline=datetime(2026, 4, 15))
    t2 = Task(user_id=user_id, title="Algorithm Practice", deadline=datetime(2026, 4, 10))
    n1 = Note(user_id=user_id, title="Exam Strategy", content="Focus on DP and Graphs.")
    r1 = Resource(user_id=user_id, title="Flask Docs", url="https://flask.palletsprojects.com/")
    
    db.session.add_all([t1, t2, n1, r1])
    db.session.commit()
    return jsonify({"msg": "Data seeded successfully"})

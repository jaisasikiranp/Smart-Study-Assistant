from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from models import db, Task, User
from functools import wraps
from datetime import datetime, timedelta

tasks_bp = Blueprint('tasks', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Support for desktop assistant via token
        token = request.headers.get('X-Assistant-Token')
        if token == 'SMART-STUDY-2026':
            if 'user_id' not in session:
                session['user_id'] = 1  # Default to user 1 for assistant
            return f(*args, **kwargs)
            
        if 'user_id' not in session:
            flash('Please log in to manage your tasks.', 'error')
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@tasks_bp.context_processor
def inject_now():
    return {'now': datetime.now(), 'timedelta': timedelta}

@tasks_bp.route('/tasks')
@login_required
def list_tasks():
    user_id = session['user_id']
    user = User.query.get(user_id)
    # Sort by deadline, then status (pending first)
    tasks = Task.query.filter_by(user_id=user_id).order_by(Task.status.desc(), Task.deadline.asc()).all()
    return render_template('tasks.html', tasks=tasks, user=user)

@tasks_bp.route('/tasks/add', methods=['POST'])
@login_required
def add_task():
    title = request.form.get('title')
    description = request.form.get('description')
    deadline_str = request.form.get('deadline')
    deadline_date = request.form.get('deadline_date')
    deadline_time = request.form.get('deadline_time')
    user_id = session['user_id']
    
    if not title:
        flash('Task title is required.', 'error')
        return redirect(url_for('tasks.list_tasks'))
        
    deadline = None
    if deadline_date:
        # Clean and normalize time string (e.g., "at 4:00 p.m." -> "4:00 PM")
        t_raw = (deadline_time or '00:00').lower()
        # Remove filler words
        for filler in ['.', 'at', 'around', 'by', 'o\'clock']:
            t_raw = t_raw.replace(filler, '')
        
        t_str = "".join(t_raw.split()) # Remove all whitespace for easier matching
        
        # Add a space before AM/PM for strptime if it's missing (e.g. "4pm" -> "4 PM")
        if t_str.endswith('am') or t_str.endswith('pm'):
             t_str = t_str[:-2] + ' ' + t_str[-2:]
        t_str = t_str.upper()

        parse_success = False
        # Try various formats commonly heard via voice
        # %I:%M %p = 04:00 PM, %I %p = 4 PM, %H:%M = 16:00
        for fmt in ['%I:%M %p', '%I %p', '%H:%M', '%H']:
            try:
                dt_part = datetime.strptime(t_str, fmt).time()
                d_part = datetime.strptime(deadline_date, '%Y-%m-%d').date()
                deadline = datetime.combine(d_part, dt_part)
                parse_success = True
                break
            except ValueError:
                continue
        
        if not parse_success:
            # More robust date parsing for voice inputs like "May 10th"
            d_str = deadline_date.lower()
            for suffix in ['st', 'nd', 'rd', 'th']:
                d_str = d_str.replace(suffix, '')
            
            # Try parsing with various date formats
            date_formats = [
                '%Y-%m-%d',     # 2026-05-10
                '%B %d',        # May 10
                '%d %B',        # 10 May
                '%b %d',        # May 10 (short)
                '%d %b',        # 10 May (short)
                '%m-%d',        # 05-10
            ]
            
            for d_fmt in date_formats:
                try:
                    d_obj = datetime.strptime(d_str, d_fmt)
                    # If year is not in format, it defaults to 1900. Set to 2026.
                    if d_obj.year == 1900:
                        d_obj = d_obj.replace(year=2026)
                    
                    # If we had a time successfully parsed, combine them
                    if 'dt_part' in locals() and dt_part:
                        deadline = datetime.combine(d_obj.date(), dt_part)
                    else:
                        deadline = d_obj
                    parse_success = True
                    break
                except ValueError:
                    continue
                    
        if not parse_success:
            flash('Invalid date format.', 'error')
    elif deadline_str:
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            try:
                deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
            except ValueError:
                flash('Invalid date format.', 'error')
    
    new_task = Task(user_id=user_id, title=title, description=description, deadline=deadline)
    db.session.add(new_task)
    db.session.commit()
    flash('New study goal added!', 'success')
    return redirect(url_for('tasks.list_tasks'))

@tasks_bp.route('/tasks/complete/<int:id>', methods=['POST'])
@login_required
def complete_task(id):
    task = Task.query.filter_by(id=id, user_id=session['user_id']).first()
    if not task:
        flash('Task not found.', 'error')
        return redirect(url_for('tasks.list_tasks'))
        
    task.status = 'completed'
    db.session.commit()
    flash('Task marked as completed! 🎉', 'success')
    return redirect(url_for('tasks.list_tasks'))

@tasks_bp.route('/tasks/delete/<int:id>', methods=['POST'])
@login_required
def delete_task(id):
    task = Task.query.filter_by(id=id, user_id=session['user_id']).first()
    if not task:
        flash('Access denied or task missing.', 'error')
        return redirect(url_for('tasks.list_tasks'))
        
    db.session.delete(task)
    db.session.commit()
    flash('Task removed.', 'info')
    return redirect(url_for('tasks.list_tasks'))

@tasks_bp.route('/tasks/pending')
@login_required
def pending_tasks():
    user_id = session['user_id']
    tasks = Task.query.filter_by(user_id=user_id, status='pending').order_by(Task.deadline.asc()).all()
    return render_template('tasks.html', tasks=tasks, show_all=False)

@tasks_bp.route('/tasks/upcoming')
@login_required
def upcoming_tasks():
    user_id = session['user_id']
    # Filter only tasks with deadlines
    tasks = Task.query.filter(
        db.and_(Task.user_id == user_id, Task.deadline != None)
    ).order_by(Task.deadline.asc()).all()
    return render_template('tasks.html', tasks=tasks, filter='upcoming')

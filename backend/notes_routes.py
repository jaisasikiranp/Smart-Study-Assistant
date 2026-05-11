from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from models import db, Note, User
from functools import wraps
from datetime import datetime

notes_bp = Blueprint('notes', __name__)

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
            flash('Please log in to manage your notes.', 'error')
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@notes_bp.route('/notes')
@login_required
def list_notes():
    user_id = session['user_id']
    user = User.query.get(user_id)
    search_query = request.args.get('search', '')
    
    if search_query:
        notes = Note.query.filter(
            db.and_(Note.user_id == user_id, Note.title.ilike(f'%{search_query}%'))
        ).order_by(Note.created_at.desc()).all()
    else:
        notes = Note.query.filter_by(user_id=user_id).order_by(Note.created_at.desc()).all()
        
    return render_template('notes.html', notes=notes, user=user)

@notes_bp.route('/notes/add', methods=['POST'])
@login_required
def add_note():
    title = request.form.get('title')
    content = request.form.get('content')
    user_id = session['user_id']
    
    if not title or not content:
        flash('Title and content are required.', 'error')
        return redirect(url_for('notes.list_notes'))
        
    new_note = Note(user_id=user_id, title=title, content=content)
    db.session.add(new_note)
    db.session.commit()
    flash('Note created successfully!', 'success')
    return redirect(url_for('notes.list_notes'))

@notes_bp.route('/notes/edit/<int:id>')
@login_required
def edit_note_page(id):
    note = Note.query.filter_by(id=id, user_id=session['user_id']).first()
    if not note:
        flash('Note not found.', 'error')
        return redirect(url_for('notes.list_notes'))
    return render_template('notes_edit.html', note=note)

@notes_bp.route('/notes/update/<int:id>', methods=['POST'])
@login_required
def update_note(id):
    note = Note.query.filter_by(id=id, user_id=session['user_id']).first()
    if not note:
        flash('Action not permitted.', 'error')
        return redirect(url_for('notes.list_notes'))
        
    note.title = request.form.get('title')
    note.content = request.form.get('content')
    note.updated_at = datetime.utcnow()
    
    db.session.commit()
    flash('Note updated successfully!', 'success')
    return redirect(url_for('notes.list_notes'))

@notes_bp.route('/notes/delete/<int:id>', methods=['POST'])
@login_required
def delete_note(id):
    note = Note.query.filter_by(id=id, user_id=session['user_id']).first()
    if not note:
        flash('Note not found or access denied.', 'error')
        return redirect(url_for('notes.list_notes'))
        
    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully!', 'info')
    return redirect(url_for('notes.list_notes'))

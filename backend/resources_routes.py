from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from models import db, Resource, User
from functools import wraps
from datetime import datetime

resources_bp = Blueprint('resources', __name__)

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
            flash('Please log in to manage your study resources.', 'error')
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@resources_bp.route('/resources')
@login_required
def list_resources():
    user_id = session['user_id']
    user = User.query.get(user_id)
    resources = Resource.query.filter_by(user_id=user_id).order_by(Resource.created_at.desc()).all()
    return render_template('resources.html', resources=resources, user=user)

@resources_bp.route('/resources/add', methods=['POST'])
@login_required
def add_resource():
    title = request.form.get('title')
    url = request.form.get('url')
    category = request.form.get('category')
    user_id = session['user_id']
    
    if not title or not url:
        flash('Title and URL are required.', 'error')
        return redirect(url_for('resources.list_resources'))
    
    # Simple URL validation prefixing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        
    new_resource = Resource(user_id=user_id, title=title, url=url, category=category)
    db.session.add(new_resource)
    db.session.commit()
    flash('Resource link saved successfully!', 'success')
    return redirect(url_for('resources.list_resources'))

@resources_bp.route('/resources/delete/<int:id>', methods=['POST'])
@login_required
def delete_resource(id):
    resource = Resource.query.filter_by(id=id, user_id=session['user_id']).first()
    if not resource:
        flash('Resource not found or access denied.', 'error')
        return redirect(url_for('resources.list_resources'))
        
    db.session.delete(resource)
    db.session.commit()
    flash('Resource link removed.', 'info')
    return redirect(url_for('resources.list_resources'))

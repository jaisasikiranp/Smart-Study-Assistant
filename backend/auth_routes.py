from flask import Blueprint, request, render_template, redirect, url_for, session, flash, jsonify
from models import db, User
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))
    return redirect(url_for('auth.login_page'))

@auth_bp.route('/register', methods=['GET'])
def register_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))
    return render_template('register.html')

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.form
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirm_password')

    if not name or not email or not password:
        flash('All fields are required.', 'error')
        return redirect(url_for('auth.register_page'))

    if password != confirm_password:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('auth.register_page'))

    user_exists = User.query.filter_by(email=email).first()
    if user_exists:
        flash('Email address already exists.', 'error')
        return redirect(url_for('auth.register_page'))

    new_user = User(name=name, email=email)
    new_user.set_password(password)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login_page'))
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('auth.register_page'))

@auth_bp.route('/login', methods=['GET'])
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard.dashboard_view'))
    return render_template('login.html')

@auth_bp.route('/login', methods=['POST'])
def login():
    email = request.form.get('email')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first()

    if user and user.check_password(password):
        session['user_id'] = user.id
        session['user_name'] = user.name
        flash(f'Welcome back, {user.name}!', 'success')
        return redirect(url_for('dashboard.dashboard_view'))
    else:
        flash('Invalid email or password.', 'error')
        return redirect(url_for('auth.login_page'))

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Successfully logged out.', 'info')
    return redirect(url_for('auth.login_page'))


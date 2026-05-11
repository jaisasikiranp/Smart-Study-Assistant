import os
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from models import db, Course, CoursePDF, User
from functools import wraps
from datetime import datetime

course_bp = Blueprint('courses', __name__)

# Config for PDF uploads
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../uploads')
ALLOWED_EXTENSIONS = {'pdf'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function

# 1. PAGE RENDER
@course_bp.route('/courses/manager')
def manager_view():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    user = User.query.get(session['user_id'])
    return render_template('courses.html', user=user)

# 2. API: GET ALL COURSES (FOR SEARCH & AJAX)
@course_bp.route('/courses', methods=['GET'])
@login_required
def get_courses():
    user_id = session['user_id']
    courses = Course.query.filter_by(user_id=user_id).order_by(Course.created_at.desc()).all()
    return jsonify([{
        "id": c.id,
        "title": c.title,
        "description": c.description,
        "created_at": c.created_at.isoformat()
    } for c in courses])

# 3. API: ADD COURSE
@course_bp.route('/add_course', methods=['POST'])
@login_required
def add_course():
    data = request.get_json()
    title = data.get('title')
    description = data.get('description')
    
    if not title:
        return jsonify({"error": "Title is required"}), 400
        
    new_course = Course(user_id=session['user_id'], title=title, description=description)
    db.session.add(new_course)
    db.session.commit()
    
    return jsonify({
        "id": new_course.id,
        "title": new_course.title,
        "description": new_course.description
    }), 201

# 4. API: GET SINGLE COURSE DETAILS + PDFS
@course_bp.route('/courses/<int:id>', methods=['GET'])
@login_required
def get_course_detail(id):
    course = Course.query.filter_by(id=id, user_id=session['user_id']).first()
    if not course:
        return jsonify({"error": "Course not found"}), 404
        
    pdfs = CoursePDF.query.filter_by(course_id=id).all()
    return jsonify({
        "id": course.id,
        "title": course.title,
        "description": course.description,
        "pdfs": [{
            "id": p.id,
            "filename": p.filename,
            "filepath": url_for('courses.download_pdf', filename=p.filename, _external=True)
        } for p in pdfs]
    })

# 5. API: UPLOAD PDF
@course_bp.route('/upload_pdf/<int:course_id>', methods=['POST'])
@login_required
def upload_pdf(course_id):
    course = Course.query.filter_by(id=course_id, user_id=session['user_id']).first()
    if not course:
        return jsonify({"error": "Course not found"}), 404
        
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
        
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{course_id}_{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        new_pdf = CoursePDF(course_id=course_id, filename=file.filename, filepath=filename)
        db.session.add(new_pdf)
        db.session.commit()
        
        return jsonify({"message": "File uploaded successfully", "filename": file.filename}), 201
        
    return jsonify({"error": "Invalid file type. Only PDFs allowed."}), 400

# 6. DOWNLOAD/VIEW PDF
@course_bp.route('/download/<filename>')
def download_pdf(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

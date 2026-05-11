import os
from flask import Flask
from models import db
from auth_routes import auth_bp
from dashboard_routes import dashboard_bp
from notes_routes import notes_bp
from tasks_routes import tasks_bp
from resources_routes import resources_bp
from course_routes import course_bp
from calendar_routes import calendar_bp

def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    
    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'final_planner.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'dev-secret-key-change-this-for-production'

    # Initialize DB
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(notes_bp)
    app.register_blueprint(tasks_bp)
    app.register_blueprint(resources_bp)
    app.register_blueprint(course_bp)
    app.register_blueprint(calendar_bp)

    with app.app_context():
        db.create_all()

    @app.context_processor
    def inject_utilities():
        from datetime import datetime, timedelta
        return {'now': datetime.utcnow(), 'timedelta': timedelta}

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)

import os
from flask import Flask, render_template
from app.config import Config
from app.models import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.routes.student import student_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp

    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', error_message="Page not found"), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('base.html', error_message="An internal server error occurred"), 500

    # Ensure database tables and auto-seed on startup if empty
    with app.app_context():
        db.create_all()
        # Check if database is empty and auto-seed if needed
        from app.models import Student, WordList
        if not Student.query.first() or not WordList.query.first():
            from app.services.seeder import seed_database
            try:
                seed_database(app=app, force=False)
            except Exception as e:
                print(f"Auto-seed notification: {e}")

    return app

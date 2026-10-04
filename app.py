"""Application entry point.  Run with:  python app.py"""
import os
import sqlite3
from flask import Flask, render_template, session, g
from flask_wtf.csrf import CSRFError
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from config import Config
from extensions import db, csrf


@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, _record):
    """SQLite ignores foreign keys unless we switch them on."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    os.makedirs(Config.EXPORT_FOLDER, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    from routes.auth import auth_bp
    from routes.student import student_bp
    from routes.admin import admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    @app.before_request
    def load_logged_in_user():
        """Make the logged-in user available as g.user (None if nobody is logged in)."""
        from models import User
        user_id = session.get("user_id")
        g.user = db.session.get(User, user_id) if user_id else None
        if user_id and g.user is None:
            session.clear()  # account was deleted

    @app.context_processor
    def inject_globals():
        from datetime import datetime
        return {"current_user": g.get("user"), "cfg": Config, "now_year": datetime.now().year}

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
        return response

    # ---- friendly error pages ----
    @app.errorhandler(403)
    def forbidden(_e):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(CSRFError)
    def csrf_error(_e):
        return render_template("errors/400.html"), 400

    @app.errorhandler(500)
    def server_error(_e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(SQLAlchemyError)
    def database_error(_e):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    # Create tables + default admin automatically on first run
    with app.app_context():
        from init_db import initialize_database
        initialize_database()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)

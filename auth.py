"""Public pages + register / login / logout for students and admins."""
from datetime import datetime, timedelta
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, session, g)
from sqlalchemy.exc import SQLAlchemyError
from config import Config
from extensions import db
from models import User
from utils import EMAIL_RE, validate_new_password

auth_bp = Blueprint("auth", __name__)

# Remembers failed login attempts in memory: {email: [count, locked_until]}
_failed_logins = {}


def _locked_minutes(email):
    entry = _failed_logins.get(email)
    if entry and entry[1] and entry[1] > datetime.utcnow():
        return int((entry[1] - datetime.utcnow()).total_seconds() // 60) + 1
    return 0


def _register_failure(email):
    entry = _failed_logins.setdefault(email, [0, None])
    entry[0] += 1
    if entry[0] >= Config.MAX_LOGIN_ATTEMPTS:
        entry[1] = datetime.utcnow() + timedelta(minutes=Config.LOCKOUT_MINUTES)
        entry[0] = 0


@auth_bp.route("/")
def index():
    return render_template("index.html")


@auth_bp.route("/about")
def about():
    return render_template("about.html")


def _handle_login(expected_role, template, success_endpoint, other_login_endpoint):
    """One login routine reused by student and admin login pages."""
    if g.user is not None:
        return redirect(url_for("admin.dashboard" if g.user.role == "admin" else "student.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please enter both email and password.", "danger")
            return render_template(template, email=email)

        wait = _locked_minutes(email)
        if wait:
            flash(f"Too many failed attempts. Try again in about {wait} minute(s).", "danger")
            return render_template(template, email=email)

        try:
            user = User.query.filter_by(email=email).first()
        except SQLAlchemyError:
            flash("Something went wrong while reading the database. Please try again.", "danger")
            return render_template(template, email=email)

        if user is None or not user.check_password(password):
            _register_failure(email)
            flash("Invalid email or password.", "danger")
            return render_template(template, email=email)

        if user.role != expected_role:
            flash("This account cannot log in here. Please use the "
                  f"{'Admin' if user.role == 'admin' else 'Student'} Login page.", "warning")
            return redirect(url_for(other_login_endpoint))

        _failed_logins.pop(email, None)
        session.clear()  # fresh session after login
        session["user_id"] = user.id
        session["role"] = user.role
        session.permanent = True
        flash(f"Welcome back, {user.name}!", "success")
        return redirect(url_for(success_endpoint))

    return render_template(template, email="")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    return _handle_login("student", "login.html", "student.dashboard", "auth.admin_login")


@auth_bp.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    return _handle_login("admin", "admin_login.html", "admin.dashboard", "auth.login")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user is not None:
        return redirect(url_for("student.dashboard" if g.user.role == "student" else "admin.dashboard"))

    if request.method == "POST":
        form = request.form
        name = form.get("name", "").strip()
        student_id = form.get("student_id", "").strip().upper()
        email = form.get("email", "").strip().lower()
        department = form.get("department", "").strip()
        year = form.get("year", "").strip()
        password = form.get("password", "")
        confirm = form.get("confirm_password", "")

        errors = []
        if not (2 <= len(name) <= 100):
            errors.append("Full name must be between 2 and 100 characters.")
        if not (3 <= len(student_id) <= 30) or not student_id.replace("-", "").replace("_", "").isalnum():
            errors.append("Student ID must be 3-30 letters/numbers.")
        if not EMAIL_RE.match(email):
            errors.append("Please enter a valid email address.")
        if department not in Config.DEPARTMENTS:
            errors.append("Please choose your department.")
        if year not in Config.YEARS:
            errors.append("Please choose your year.")
        errors += validate_new_password(password, confirm)

        if student_id and User.query.filter_by(student_id=student_id).first():
            errors.append("This Student ID is already registered.")
        if email and User.query.filter_by(email=email).first():
            errors.append("This email is already registered.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html", form=form)

        try:
            user = User(name=name, student_id=student_id, email=email,
                        department=department, year=year, role="student")
            user.set_password(password)  # stores a hash, never the plain password
            db.session.add(user)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("Could not create your account. Please try again.", "danger")
            return render_template("register.html", form=form)

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form={})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.index"))

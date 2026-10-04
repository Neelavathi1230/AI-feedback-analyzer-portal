"""Helper functions shared by the route files: access control + form validation."""
import re
from functools import wraps
from flask import g, redirect, url_for, flash, abort
from config import Config

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def student_required(view):
    """Only a logged-in student may open the page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("auth.login"))
        if g.user.role != "student":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    """Only a logged-in admin may open the page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            flash("Please log in as admin to continue.", "warning")
            return redirect(url_for("auth.admin_login"))
        if g.user.role != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def validate_feedback_form(form):
    """Server-side validation. Returns (errors_list, cleaned_dict)."""
    errors = []
    category = form.get("category", "").strip()
    department = form.get("department", "").strip()
    subject = form.get("subject", "").strip()
    faculty = form.get("faculty", "").strip()
    comment = form.get("comment", "").strip()
    rating_raw = form.get("rating", "").strip()

    if category not in Config.CATEGORIES:
        errors.append("Please choose a valid feedback category.")
    if department not in Config.DEPARTMENTS:
        errors.append("Please choose a valid department.")
    if not (2 <= len(subject) <= 100):
        errors.append("Subject / Course must be between 2 and 100 characters.")
    if len(faculty) > 100:
        errors.append("Faculty name must be at most 100 characters.")

    rating = None
    if rating_raw.isdigit() and 1 <= int(rating_raw) <= 5:
        rating = int(rating_raw)
    else:
        errors.append("Please select a rating from 1 to 5.")

    if len(comment) < Config.COMMENT_MIN:
        errors.append(f"Comment must be at least {Config.COMMENT_MIN} characters.")
    elif len(comment) > Config.COMMENT_MAX:
        errors.append(f"Comment must be at most {Config.COMMENT_MAX} characters.")

    cleaned = {
        "category": category, "department": department, "subject": subject,
        "faculty": faculty or None, "rating": rating, "comment": comment,
        "is_anonymous": form.get("is_anonymous") == "on",
    }
    return errors, cleaned


def validate_new_password(password, confirm):
    """Shared password rules. Returns a list of error messages."""
    errors = []
    if len(password) < Config.MIN_PASSWORD_LENGTH:
        errors.append(f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters long.")
    if password != confirm:
        errors.append("Password and confirm password do not match.")
    return errors


def csv_safe(value):
    """Stop spreadsheet formula injection (cells starting with = + - @)."""
    text = "" if value is None else str(value)
    if text and text[0] in "=+-@":
        return "'" + text
    return text

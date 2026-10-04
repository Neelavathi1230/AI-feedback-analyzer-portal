"""Student pages: dashboard, submit/view/edit/delete own feedback, profile."""
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, g)
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from config import Config
from extensions import db
from models import Feedback
from services.sentiment_analysis import analyze_sentiment
from utils import student_required, validate_feedback_form, validate_new_password

student_bp = Blueprint("student", __name__, url_prefix="/student")


def _own_feedback_or_404(feedback_id):
    # Filtering by user_id means a student can never open someone else's feedback.
    return Feedback.query.filter_by(id=feedback_id, user_id=g.user.id).first_or_404()


@student_bp.route("/dashboard")
@student_required
def dashboard():
    mine = Feedback.query.filter_by(user_id=g.user.id)
    total = mine.count()
    counts = dict(db.session.query(Feedback.sentiment, func.count(Feedback.id))
                  .filter(Feedback.user_id == g.user.id).group_by(Feedback.sentiment).all())
    avg = db.session.query(func.avg(Feedback.rating)).filter(Feedback.user_id == g.user.id).scalar()
    recent = mine.order_by(Feedback.created_at.desc()).limit(5).all()
    return render_template("student/dashboard.html", total=total, counts=counts,
                           avg_rating=round(avg, 2) if avg else 0, recent=recent)


@student_bp.route("/feedback/new", methods=["GET", "POST"])
@student_required
def submit_feedback():
    values = {"department": g.user.department}
    if request.method == "POST":
        errors, cleaned = validate_feedback_form(request.form)
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("student/feedback_form.html", values=request.form, fb=None)
        try:
            label, score = analyze_sentiment(cleaned["comment"])
            fb = Feedback(user_id=g.user.id, sentiment=label, sentiment_score=score, **cleaned)
            db.session.add(fb)
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("Could not save your feedback. Please try again.", "danger")
            return render_template("student/feedback_form.html", values=request.form, fb=None)
        flash(f"Feedback submitted! Detected sentiment: {label}.", "success")
        return redirect(url_for("student.feedback_detail", feedback_id=fb.id))
    return render_template("student/feedback_form.html", values=values, fb=None)


@student_bp.route("/feedback")
@student_required
def my_feedback():
    page = request.args.get("page", 1, type=int)
    sentiment = request.args.get("sentiment", "")
    query = Feedback.query.filter_by(user_id=g.user.id)
    if sentiment in Config.SENTIMENTS:
        query = query.filter_by(sentiment=sentiment)
    pagination = query.order_by(Feedback.created_at.desc()).paginate(
        page=page, per_page=Config.PER_PAGE, error_out=False)
    args = {"sentiment": sentiment} if sentiment else {}
    return render_template("student/my_feedback.html", pagination=pagination,
                           sentiment=sentiment, args=args)


@student_bp.route("/feedback/<int:feedback_id>")
@student_required
def feedback_detail(feedback_id):
    return render_template("student/feedback_detail.html", fb=_own_feedback_or_404(feedback_id))


@student_bp.route("/feedback/<int:feedback_id>/edit", methods=["GET", "POST"])
@student_required
def edit_feedback(feedback_id):
    fb = _own_feedback_or_404(feedback_id)
    if request.method == "POST":
        errors, cleaned = validate_feedback_form(request.form)
        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("student/feedback_form.html", values=request.form, fb=fb)
        try:
            for key, value in cleaned.items():
                setattr(fb, key, value)
            fb.sentiment, fb.sentiment_score = analyze_sentiment(fb.comment)  # re-analyse
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            flash("Could not update your feedback. Please try again.", "danger")
            return render_template("student/feedback_form.html", values=request.form, fb=fb)
        flash("Feedback updated and sentiment re-analysed.", "success")
        return redirect(url_for("student.feedback_detail", feedback_id=fb.id))
    values = {"category": fb.category, "department": fb.department, "subject": fb.subject,
              "faculty": fb.faculty or "", "rating": str(fb.rating), "comment": fb.comment,
              "is_anonymous": "on" if fb.is_anonymous else ""}
    return render_template("student/feedback_form.html", values=values, fb=fb)


@student_bp.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
@student_required
def delete_feedback(feedback_id):
    fb = _own_feedback_or_404(feedback_id)
    try:
        db.session.delete(fb)
        db.session.commit()
        flash("Feedback deleted.", "info")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Could not delete the feedback. Please try again.", "danger")
    return redirect(url_for("student.my_feedback"))


@student_bp.route("/profile", methods=["GET", "POST"])
@student_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "details":
            name = request.form.get("name", "").strip()
            department = request.form.get("department", "").strip()
            year = request.form.get("year", "").strip()
            if not (2 <= len(name) <= 100) or department not in Config.DEPARTMENTS or year not in Config.YEARS:
                flash("Please enter a valid name, department and year.", "danger")
            else:
                try:
                    g.user.name, g.user.department, g.user.year = name, department, year
                    db.session.commit()
                    flash("Profile updated.", "success")
                except SQLAlchemyError:
                    db.session.rollback()
                    flash("Could not update profile.", "danger")
        elif action == "password":
            current = request.form.get("current_password", "")
            new = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")
            if not g.user.check_password(current):
                flash("Current password is incorrect.", "danger")
            else:
                errors = validate_new_password(new, confirm)
                if errors:
                    for e in errors:
                        flash(e, "danger")
                else:
                    try:
                        g.user.set_password(new)
                        db.session.commit()
                        flash("Password changed successfully.", "success")
                    except SQLAlchemyError:
                        db.session.rollback()
                        flash("Could not change password.", "danger")
        return redirect(url_for("student.profile"))
    return render_template("student/profile.html")

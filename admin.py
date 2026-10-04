"""Admin pages: dashboard, feedback management, students, analytics, reports."""
import csv
import io
import os
from datetime import datetime, timedelta
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, g, Response)
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from config import Config
from extensions import db
from models import User, Feedback
from utils import admin_required, csv_safe, validate_new_password

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

FILTER_KEYS = ["q", "sentiment", "category", "department", "rating", "date_from", "date_to"]


def filtered_query(args):
    """Build a Feedback query from the filters in the URL. All filters work together."""
    query = Feedback.query
    q = args.get("q", "").strip()
    if q:
        like = f"%{q}%"
        query = query.filter(or_(
            Feedback.comment.ilike(like), Feedback.category.ilike(like),
            Feedback.department.ilike(like), Feedback.subject.ilike(like),
            Feedback.faculty.ilike(like), Feedback.sentiment.ilike(like)))
    if args.get("sentiment") in Config.SENTIMENTS:
        query = query.filter(Feedback.sentiment == args["sentiment"])
    if args.get("category") in Config.CATEGORIES:
        query = query.filter(Feedback.category == args["category"])
    if args.get("department") in Config.DEPARTMENTS:
        query = query.filter(Feedback.department == args["department"])
    rating = args.get("rating", "")
    if rating.isdigit() and 1 <= int(rating) <= 5:
        query = query.filter(Feedback.rating == int(rating))
    try:
        if args.get("date_from"):
            query = query.filter(Feedback.created_at >= datetime.strptime(args["date_from"], "%Y-%m-%d"))
        if args.get("date_to"):
            query = query.filter(Feedback.created_at < datetime.strptime(args["date_to"], "%Y-%m-%d") + timedelta(days=1))
    except ValueError:
        pass  # ignore badly typed dates
    return query


def build_stats():
    """All numbers used by the dashboard and analytics pages (real database data)."""
    total = Feedback.query.count()
    sentiment_counts = dict(db.session.query(Feedback.sentiment, func.count(Feedback.id))
                            .group_by(Feedback.sentiment).all())
    positive = sentiment_counts.get("Positive", 0)
    neutral = sentiment_counts.get("Neutral", 0)
    negative = sentiment_counts.get("Negative", 0)
    avg_rating = db.session.query(func.avg(Feedback.rating)).scalar() or 0

    cat_rows = db.session.query(Feedback.category, func.count(Feedback.id), func.avg(Feedback.rating)) \
        .group_by(Feedback.category).all()
    categories = [{"name": c, "count": n, "avg": round(a, 2)} for c, n, a in cat_rows]
    categories.sort(key=lambda x: x["count"], reverse=True)

    rating_counts = dict(db.session.query(Feedback.rating, func.count(Feedback.id))
                         .group_by(Feedback.rating).all())

    dept_rows = db.session.query(Feedback.department, func.count(Feedback.id),
                                 func.avg(Feedback.rating), func.avg(Feedback.sentiment_score)) \
        .group_by(Feedback.department).all()
    departments = [{"name": d, "count": n, "avg": round(a, 2), "score": round(s, 3)}
                   for d, n, a, s in dept_rows]
    departments.sort(key=lambda x: x["count"], reverse=True)

    month_expr = func.strftime("%Y-%m", Feedback.created_at)
    month_rows = db.session.query(month_expr, func.count(Feedback.id)) \
        .group_by(month_expr).order_by(month_expr).all()[-12:]

    def pct(n):
        return round(n * 100 / total, 1) if total else 0

    return {
        "total_students": User.query.filter_by(role="student").count(),
        "total": total, "positive": positive, "neutral": neutral, "negative": negative,
        "positive_pct": pct(positive), "neutral_pct": pct(neutral), "negative_pct": pct(negative),
        "avg_rating": round(avg_rating, 2),
        "categories": categories,
        "most_common": categories[0] if categories else None,
        "highest_rated": max(categories, key=lambda x: x["avg"]) if categories else None,
        "lowest_rated": min(categories, key=lambda x: x["avg"]) if categories else None,
        "departments": departments,
        "chart": {
            "sentiment": [positive, neutral, negative],
            "category_labels": [c["name"] for c in categories],
            "category_counts": [c["count"] for c in categories],
            "category_avg": [c["avg"] for c in categories],
            "rating_counts": [rating_counts.get(i, 0) for i in range(1, 6)],
            "month_labels": [m for m, _ in month_rows],
            "month_counts": [n for _, n in month_rows],
            "dept_labels": [d["name"] for d in departments],
            "dept_counts": [d["count"] for d in departments],
            "dept_avg": [d["avg"] for d in departments],
        },
    }


@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    stats = build_stats()
    recent = Feedback.query.order_by(Feedback.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html", stats=stats, recent=recent)


@admin_bp.route("/feedback")
@admin_required
def feedback_list():
    page = request.args.get("page", 1, type=int)
    sort = request.args.get("sort", "newest")
    order = {
        "newest": Feedback.created_at.desc(), "oldest": Feedback.created_at.asc(),
        "rating_high": Feedback.rating.desc(), "rating_low": Feedback.rating.asc(),
        "score_high": Feedback.sentiment_score.desc(), "score_low": Feedback.sentiment_score.asc(),
    }.get(sort, Feedback.created_at.desc())
    pagination = filtered_query(request.args).order_by(order, Feedback.id.desc()).paginate(
        page=page, per_page=Config.PER_PAGE, error_out=False)
    # filters that must be kept when moving between pages
    args = {k: request.args[k] for k in FILTER_KEYS + ["sort"] if request.args.get(k)}
    return render_template("admin/feedback.html", pagination=pagination, args=args, sort=sort)


@admin_bp.route("/feedback/<int:feedback_id>")
@admin_required
def feedback_detail(feedback_id):
    fb = db.get_or_404(Feedback, feedback_id)
    return render_template("admin/feedback_detail.html", fb=fb)


@admin_bp.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
@admin_required
def delete_feedback(feedback_id):
    fb = db.get_or_404(Feedback, feedback_id)
    try:
        db.session.delete(fb)
        db.session.commit()
        flash("Feedback deleted.", "info")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Could not delete the feedback.", "danger")
    return redirect(url_for("admin.feedback_list"))


@admin_bp.route("/students")
@admin_required
def students():
    page = request.args.get("page", 1, type=int)
    q = request.args.get("q", "").strip()
    query = User.query.filter_by(role="student")
    if q:
        like = f"%{q}%"
        query = query.filter(or_(User.name.ilike(like), User.student_id.ilike(like),
                                 User.email.ilike(like), User.department.ilike(like)))
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=Config.PER_PAGE, error_out=False)
    return render_template("admin/students.html", pagination=pagination, q=q,
                           args={"q": q} if q else {})


@admin_bp.route("/students/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_student(user_id):
    user = db.get_or_404(User, user_id)
    if user.role != "student":
        flash("Only student accounts can be deleted here.", "danger")
        return redirect(url_for("admin.students"))
    try:
        db.session.delete(user)  # also deletes this student's feedback
        db.session.commit()
        flash(f"Student '{user.name}' and their feedback were deleted.", "info")
    except SQLAlchemyError:
        db.session.rollback()
        flash("Could not delete the student.", "danger")
    return redirect(url_for("admin.students"))


@admin_bp.route("/analytics")
@admin_required
def analytics():
    return render_template("admin/analytics.html", stats=build_stats())


@admin_bp.route("/reports")
@admin_required
def reports():
    query = filtered_query(request.args)
    count = query.count()
    preview = query.order_by(Feedback.created_at.desc()).limit(10).all()
    args = {k: request.args[k] for k in FILTER_KEYS if request.args.get(k)}
    sample_count = User.query.filter_by(is_sample=True).count()
    return render_template("admin/reports.html", count=count, preview=preview,
                           args=args, sample_count=sample_count)


@admin_bp.route("/reports/download")
@admin_required
def download_csv():
    rows = filtered_query(request.args).order_by(Feedback.created_at.desc()).all()
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Feedback ID", "Category", "Department", "Subject", "Faculty",
                     "Rating", "Sentiment", "Sentiment Score", "Date"])
    for f in rows:  # no student identity is written, anonymous or not
        writer.writerow([f.id, csv_safe(f.category), csv_safe(f.department), csv_safe(f.subject),
                         csv_safe(f.faculty), f.rating, f.sentiment, f.sentiment_score,
                         f.created_at.strftime("%Y-%m-%d %H:%M")])
    data = "\ufeff" + buffer.getvalue()  # BOM so Excel opens UTF-8 correctly
    filename = f"feedback_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    try:  # also keep a copy in the exports folder
        os.makedirs(Config.EXPORT_FOLDER, exist_ok=True)
        with open(os.path.join(Config.EXPORT_FOLDER, filename), "w", encoding="utf-8", newline="") as fh:
            fh.write(data)
    except OSError:
        pass
    return Response(data, mimetype="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})


@admin_bp.route("/sample-data/load", methods=["POST"])
@admin_required
def load_sample():
    from init_db import create_sample_data
    users, feedback = create_sample_data()
    if users:
        flash(f"Sample data loaded: {users} students and {feedback} feedback entries.", "success")
    else:
        flash("Sample data is already loaded.", "info")
    return redirect(url_for("admin.reports"))


@admin_bp.route("/sample-data/remove", methods=["POST"])
@admin_required
def remove_sample():
    from init_db import remove_sample_data
    users = remove_sample_data()
    flash(f"Removed {users} sample students and all of their feedback.", "info")
    return redirect(url_for("admin.reports"))


@admin_bp.route("/profile", methods=["GET", "POST"])
@admin_required
def profile():
    if request.method == "POST":
        action = request.form.get("action")
        if action == "details":
            name = request.form.get("name", "").strip()
            if not (2 <= len(name) <= 100):
                flash("Name must be between 2 and 100 characters.", "danger")
            else:
                try:
                    g.user.name = name
                    db.session.commit()
                    flash("Profile updated.", "success")
                except SQLAlchemyError:
                    db.session.rollback()
                    flash("Could not update profile.", "danger")
        elif action == "password":
            if not g.user.check_password(request.form.get("current_password", "")):
                flash("Current password is incorrect.", "danger")
            else:
                errors = validate_new_password(request.form.get("new_password", ""),
                                               request.form.get("confirm_password", ""))
                if errors:
                    for e in errors:
                        flash(e, "danger")
                else:
                    try:
                        g.user.set_password(request.form["new_password"])
                        db.session.commit()
                        flash("Password changed successfully.", "success")
                    except SQLAlchemyError:
                        db.session.rollback()
                        flash("Could not change password.", "danger")
        return redirect(url_for("admin.profile"))
    return render_template("admin/profile.html")

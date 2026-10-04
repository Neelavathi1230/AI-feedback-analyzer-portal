"""
Database setup helper.

    python init_db.py                  create tables + default admin
    python init_db.py --sample         also add demo students and feedback
    python init_db.py --remove-sample  delete the demo data only
    python init_db.py --reset          delete everything and start again
"""
import os
import random
import sys
from datetime import datetime, timedelta
from config import Config
from extensions import db
from models import User, Feedback
from services.sentiment_analysis import analyze_sentiment


def initialize_database():
    """Create all tables and the default admin account (safe to run many times)."""
    db.create_all()
    admin = User.query.filter_by(role="admin").first()
    if admin is None:
        admin = User(name=Config.DEFAULT_ADMIN_NAME, email=Config.DEFAULT_ADMIN_EMAIL.lower(),
                     role="admin", student_id=None)
        admin.set_password(Config.DEFAULT_ADMIN_PASSWORD)
        db.session.add(admin)
        db.session.commit()
        print(f"Default admin created: {Config.DEFAULT_ADMIN_EMAIL}")


# ---------- sample data ----------
SAMPLE_STUDENTS = [
    ("Aarav Sharma", "Computer Science", "2nd Year"), ("Diya Patel", "Information Technology", "3rd Year"),
    ("Rohan Mehta", "Electronics", "1st Year"), ("Sneha Iyer", "Mechanical", "4th Year"),
    ("Karan Verma", "Civil", "2nd Year"), ("Ananya Rao", "Computer Science", "3rd Year"),
    ("Vikram Singh", "Electrical", "2nd Year"), ("Meera Nair", "Business Administration", "1st Year"),
    ("Arjun Reddy", "Information Technology", "4th Year"), ("Priya Das", "Computer Science", "1st Year"),
    ("Imran Khan", "Mechanical", "3rd Year"), ("Lakshmi Menon", "Electronics", "2nd Year"),
]

# (category, subject, faculty, rating, comment)
SAMPLE_FEEDBACK = [
    ("Teaching", "Data Structures", "Dr. Rao", 5, "I really enjoyed the teaching and the faculty explained everything clearly."),
    ("Teaching", "Operating Systems", "Prof. Menon", 5, "Excellent lectures with great real-life examples. Very helpful and engaging."),
    ("Teaching", "Engineering Maths", "Dr. Gupta", 2, "The lectures are too fast and hard to understand. Needs improvement."),
    ("Teaching", "Thermodynamics", "Prof. Khan", 3, "The classes were okay, nothing special."),
    ("Faculty", "Database Systems", "Dr. Iyer", 5, "The professor is friendly, supportive and always available for doubts."),
    ("Faculty", "Networks", "Prof. Nair", 1, "The teacher is rude and unhelpful during doubt sessions."),
    ("Faculty", "Digital Electronics", "Dr. Kapoor", 3, "Average teaching style, the faculty is fine."),
    ("Course", "Web Technology", "Prof. Das", 5, "Great course content, very interesting and well organised."),
    ("Course", "Cloud Computing", "Dr. Bose", 4, "Good syllabus and helpful practical assignments."),
    ("Course", "Machine Design", "Prof. Singh", 2, "The syllabus is outdated and the course material is confusing."),
    ("Course", "Python Programming", "Dr. Joshi", 3, "The course was okay."),
    ("Infrastructure", "Classrooms", "", 2, "The classrooms are crowded and the projectors are often not working."),
    ("Infrastructure", "Campus Wi-Fi", "", 1, "The Wi-Fi is very slow and keeps disconnecting. Terrible experience."),
    ("Infrastructure", "Campus Buildings", "", 5, "The new campus building is modern, clean and comfortable."),
    ("Library", "Central Library", "", 5, "The library is quiet and the staff is very helpful."),
    ("Library", "Central Library", "", 2, "Not enough copies of the important textbooks and the opening hours are limited."),
    ("Library", "Digital Library", "", 3, "The digital library is average, it works fine."),
    ("Laboratory", "Electronics Lab", "", 2, "The laboratory equipment is old and needs improvement."),
    ("Laboratory", "Computer Lab", "", 4, "The computer lab has good systems and a friendly lab assistant."),
    ("Laboratory", "Physics Lab", "", 1, "Several instruments are broken and the lab is dirty."),
    ("Canteen", "Main Canteen", "", 2, "The food is overpriced and not clean."),
    ("Canteen", "Main Canteen", "", 5, "The canteen food is tasty and fresh, and the staff is polite."),
    ("Canteen", "Snack Corner", "", 3, "Canteen is okay, the prices are fair."),
    ("Hostel", "Boys Hostel", "", 1, "The hostel rooms are dirty and the water supply is irregular."),
    ("Hostel", "Girls Hostel", "", 4, "The hostel is safe and comfortable with a supportive warden."),
    ("Transportation", "College Bus", "", 2, "The bus is always late and too crowded."),
    ("Transportation", "College Bus", "", 4, "Bus service is punctual and the drivers are helpful."),
    ("Events", "Annual Fest", "", 5, "The annual fest was wonderful and very well organised!"),
    ("Events", "Tech Symposium", "", 3, "The symposium was average, some sessions were fine."),
    ("Events", "Sports Day", "", 2, "Poor planning and the schedule was confusing."),
    ("General", "College Experience", "", 5, "I love the friendly atmosphere and the supportive teachers here."),
    ("General", "College Experience", "", 3, "Overall the college is okay."),
    ("General", "Administration", "", 1, "The administration office is slow and unhelpful with certificates."),
]


def create_sample_data(seed=42):
    """Add demo students + feedback. Returns (students_added, feedback_added)."""
    if User.query.filter_by(is_sample=True).count():
        return 0, 0
    rnd = random.Random(seed)
    users = []
    for i, (name, dept, year) in enumerate(SAMPLE_STUDENTS, start=1):
        u = User(name=name, student_id=f"SMP{i:03d}", email=f"student{i}@{Config.SAMPLE_EMAIL_DOMAIN}",
                 department=dept, year=year, role="student", is_sample=True)
        u.set_password(Config.SAMPLE_PASSWORD)
        db.session.add(u)
        users.append(u)
    db.session.flush()

    count = 0
    now = datetime.utcnow()
    for round_no in range(2):  # every sample comment is used twice by different students
        for category, subject, faculty, rating, comment in SAMPLE_FEEDBACK:
            user = rnd.choice(users)
            label, score = analyze_sentiment(comment)
            created = now - timedelta(days=rnd.randint(0, 170), hours=rnd.randint(0, 23))
            db.session.add(Feedback(
                user_id=user.id, category=category, department=user.department, subject=subject,
                faculty=faculty or None, rating=max(1, min(5, rating + rnd.choice([0, 0, 0, -1, 1]) if round_no else rating)),
                comment=comment, sentiment=label, sentiment_score=score,
                is_anonymous=rnd.random() < 0.3, created_at=created, updated_at=created))
            count += 1
    db.session.commit()
    return len(users), count


def remove_sample_data():
    """Delete sample students (their feedback goes with them). Returns students removed."""
    users = User.query.filter_by(is_sample=True).all()
    for u in users:
        db.session.delete(u)
    db.session.commit()
    return len(users)


if __name__ == "__main__":
    from app import create_app
    app = create_app()
    with app.app_context():
        if "--reset" in sys.argv:
            db.drop_all()
            print("All tables dropped.")
        initialize_database()
        print("Database ready.")
        if "--remove-sample" in sys.argv:
            print(f"Removed {remove_sample_data()} sample students.")
        if "--sample" in sys.argv:
            u, f = create_sample_data()
            print(f"Sample data: {u} students, {f} feedback entries." if u else "Sample data already exists.")

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(db.Model):
    """Both students and admins live in this table; `role` tells them apart."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    student_id = db.Column(db.String(30), unique=True, nullable=True)  # admins may not have one
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    department = db.Column(db.String(100), nullable=True)
    year = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="student")  # 'student' or 'admin'
    is_sample = db.Column(db.Boolean, nullable=False, default=False)  # True for demo data
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # One user -> many feedback rows. Deleting a user deletes their feedback.
    feedback_items = db.relationship("Feedback", backref="user", lazy="dynamic",
                                     cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

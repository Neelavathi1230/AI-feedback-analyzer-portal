from datetime import datetime
from extensions import db


class Feedback(db.Model):
    __tablename__ = "feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    faculty = db.Column(db.String(100), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comment = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(10), nullable=False)  # Positive / Neutral / Negative
    sentiment_score = db.Column(db.Float, nullable=False)  # -1.0 (very negative) to +1.0
    is_anonymous = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

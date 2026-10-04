"""Central configuration. Change values here, not in many files."""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Used to sign session cookies and CSRF tokens. Change it for real deployments.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me-before-real-use")

    # SQLite database file lives next to app.py
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session cookie safety
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 2  # 2 hours

    # Default admin (created automatically the first time the app runs).
    # The only place these credentials are defined. Override with environment variables if you like.
    DEFAULT_ADMIN_NAME = os.environ.get("ADMIN_NAME", "System Administrator")
    DEFAULT_ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@college.edu")
    DEFAULT_ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "Admin@12345")

    # Sample data
    SAMPLE_PASSWORD = "Sample@123"
    SAMPLE_EMAIL_DOMAIN = "sample.edu"

    # Validation rules
    MIN_PASSWORD_LENGTH = 6
    COMMENT_MIN = 10
    COMMENT_MAX = 1000

    # Login protection: lock an email for a while after too many wrong passwords
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_MINUTES = 5

    # Pagination
    PER_PAGE = 10

    # Folder where CSV report copies are saved
    EXPORT_FOLDER = os.path.join(BASE_DIR, "exports")

    # Dropdown options used by forms, filters and validation
    CATEGORIES = ["Teaching", "Faculty", "Course", "Infrastructure", "Library",
                  "Laboratory", "Canteen", "Hostel", "Transportation", "Events", "General"]
    DEPARTMENTS = ["Computer Science", "Information Technology", "Electronics",
                   "Mechanical", "Civil", "Electrical", "Business Administration", "Other"]
    YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
    SENTIMENTS = ["Positive", "Neutral", "Negative"]

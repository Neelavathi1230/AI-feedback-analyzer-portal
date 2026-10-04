# AI-Based Student Feedback Analysis & Sentiment Monitoring Portal

A Web Technology project built with Flask, SQLite, Bootstrap 5 and Chart.js.
Students submit feedback; the portal labels each comment Positive, Neutral or Negative and shows administrators dashboards, analytics and CSV reports. Everything runs on your own computer (localhost).

## 1. Project overview
Two roles use the system:
- **Student**: registers, logs in, submits/edits/deletes feedback, sees the sentiment result of their own comments.
- **Admin**: sees dashboard charts, searches and filters all feedback, manages students, views analytics, downloads CSV reports and deletes inappropriate feedback.

## 2. Features
- Student registration with validation, hashed passwords, unique Student ID and email
- Separate student login and admin login, session authentication, role-based access control
- Login protection: an email is locked for 5 minutes after 5 wrong passwords
- CSRF protection on every form (Flask-WTF)
- Feedback form: 11 categories, department, subject, optional faculty, rating 1-5, comment (10-1000 characters), anonymous option
- Automatic sentiment label + score (-1 to +1) saved with every feedback
- Admin dashboard: 6 summary cards and 5 Chart.js charts using real database data
- Admin feedback list: search, filters (sentiment, category, department, rating, dates), sorting, pagination
- Analytics page, student management, CSV report download, admin profile
- Anonymous feedback never reveals the student to admins or in CSV files
- Friendly 400 / 403 / 404 / 500 error pages
- Sample (demo) data that can be loaded and removed in one click

## 3. Technologies used
HTML5, CSS3, JavaScript, Bootstrap 5.3, Chart.js 4 (both loaded from a CDN, so you need internet when viewing the pages), Python 3.9+, Flask 3, Flask-SQLAlchemy, Flask-WTF, SQLite, TextBlob.

## 4. Folder structure
```
AI_Feedback_Analysis_Portal/
|-- app.py              Starts the app, registers routes, error pages
|-- config.py           All settings (secret key, default admin, dropdown lists)
|-- extensions.py       db and CSRF objects shared by all files
|-- init_db.py          Creates tables, default admin, sample data
|-- utils.py            Login/role decorators and form validation helpers
|-- requirements.txt    Python packages
|-- database.db         Created automatically on first run
|-- models/             user.py, feedback.py (database tables)
|-- routes/             auth.py (public + login), student.py, admin.py
|-- services/           sentiment_analysis.py
|-- templates/          HTML pages (base.html is the shared layout)
|   |-- student/  admin/  errors/
|-- static/css/style.css, static/js/script.js, static/images/
|-- exports/            Copies of generated CSV reports
```
How files connect: `app.py` creates the Flask app and registers the three blueprints in `routes/`. Routes use the tables in `models/`, call `services/sentiment_analysis.py` when feedback is saved, and render pages from `templates/`, which all extend `base.html`.

## 5. Installation (Windows PowerShell)
1. Install Python 3.9 or newer from python.org. Tick **"Add Python to PATH"** during setup.
2. Unzip the project and open PowerShell inside the `AI_Feedback_Analysis_Portal` folder (in VS Code: Terminal > New Terminal).

## 6. Virtual environment
```powershell
python -m venv venv
venv\Scripts\activate
```
You should now see `(venv)` at the start of the prompt.

## 7. Install packages
```powershell
pip install -r requirements.txt
```

## 8. Database initialization
```powershell
python init_db.py
```
This creates `database.db` and the default admin. (The app also does this by itself on first run.)

Optional demo data:
```powershell
python init_db.py --sample          # add 12 sample students + 66 feedback entries
python init_db.py --remove-sample   # remove only the sample data
python init_db.py --reset           # wipe everything and start fresh
```
You can also load/remove sample data from the admin **Reports** page.

## 9. Run the project
```powershell
python app.py
```
Open **http://127.0.0.1:5000** in your browser. Press `Ctrl + C` in PowerShell to stop.

## 10. Student login
Register at `/register`, then log in at `/login`.
If you loaded sample data you can also use: `student1@sample.edu` ... `student12@sample.edu` with password `Sample@123`.

## 11. Admin login
Open `/admin-login` (or the "Admin" link in the navbar).
- Email: `admin@college.edu`
- Password: `Admin@12345`

These test credentials are defined only in `config.py`. Change the password from **Admin > Profile** after logging in, or set `ADMIN_EMAIL` / `ADMIN_PASSWORD` environment variables before the first run.

## 12. How sentiment analysis works
1. TextBlob gives a polarity score from -1 to +1.
2. A short list of positive/negative words and phrases typical for college feedback (for example "outdated", "needs improvement", "helpful") adjusts the score.
3. Words like "okay" or "average" with no strong words keep the result near zero.
4. Score >= 0.10 is **Positive**, <= -0.10 is **Negative**, otherwise **Neutral**.

This is a lightweight, rule-based feature, not a trained AI model. It can be wrong with sarcasm, mixed opinions or very short comments. The code is in `services/sentiment_analysis.py`.

## 13. Generate reports
Log in as admin > **Reports**. Optionally choose filters (sentiment, category, department, dates), check the preview, then click **Download CSV Report**. The CSV has Feedback ID, Category, Department, Subject, Faculty, Rating, Sentiment, Sentiment Score and Date, and no student identity. A copy is also saved in the `exports/` folder.

## 14. Common errors and solutions
| Problem | Solution |
|---|---|
| `python` is not recognized | Reinstall Python and tick "Add Python to PATH", or try `py -m venv venv` |
| `venv\Scripts\activate` is blocked ("running scripts is disabled") | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, answer Y, then activate again |
| `ModuleNotFoundError: No module named 'flask'` | The virtual environment is not active. Run `venv\Scripts\activate` then `pip install -r requirements.txt` |
| Port 5000 already in use | Change the last line of `app.py` to `app.run(debug=True, port=5001)` and open port 5001 |
| Charts or styling look missing | Bootstrap/Chart.js load from the internet (CDN). Check your connection |
| "Your form session expired" (400 page) | Refresh the page and submit again |
| Forgot the admin password | Stop the app, run `python init_db.py --reset`, and the default admin is created again (this deletes all data) |
| "Too many failed attempts" | Wait 5 minutes or restart the app |

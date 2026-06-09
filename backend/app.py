import logging
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date

from backend.config import FLASK_PORT, FLASK_DEBUG, ABSENT_HOUR, ABSENT_MINUTE
from backend.models import init_db, Session, Attendance, Student
from backend.routes.auth import auth_bp
from backend.routes.admin import admin_bp
from backend.routes.teacher import teacher_bp
from backend.routes.enroll import enroll_bp
from backend.routes.attend import attend_bp
from backend.routes.reports import reports_bp

# ── Logging ──
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# ── App ──
app = Flask(__name__)
CORS(app)

# JWT config
app.config["JWT_SECRET_KEY"] = "attendai-super-secret-key-change-in-production"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = False   # tokens don't expire (simplify for dev)
JWTManager(app)

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(enroll_bp)
app.register_blueprint(attend_bp)
app.register_blueprint(reports_bp)


# ── Auto-mark absent ──
def auto_mark_absent():
    """
    Runs daily at ABSENT_HOUR:ABSENT_MINUTE (default 10:05 AM).
    Marks all students who haven't checked in today as absent.
    """
    session = Session()
    try:
        today       = date.today()
        students    = session.query(Student).all()
        present_ids = {
            a.student_id for a in
            session.query(Attendance)
            .filter_by(date=today, status="present")
            .all()
        }

        count = 0
        for s in students:
            if s.id not in present_ids:
                existing = session.get(Attendance, (s.id, today))
                if existing:
                    existing.status = "absent"
                else:
                    session.add(Attendance(
                        student_id = s.id,
                        date       = today,
                        status     = "absent"
                    ))
                count += 1

        session.commit()
        logger.info(f"✅ Auto-marked {count} student(s) absent for {today}")

    except Exception as e:
        logger.error(f"❌ auto_mark_absent error: {e}")
        session.rollback()
    finally:
        session.close()


# ── Scheduler ──
scheduler = BackgroundScheduler()
scheduler.add_job(auto_mark_absent, "cron", hour=ABSENT_HOUR, minute=ABSENT_MINUTE)
scheduler.start()
logger.info(f"⏰ Scheduler started — auto-absent at {ABSENT_HOUR:02d}:{ABSENT_MINUTE:02d}")


# ── Entry point ──
if __name__ == "__main__":
    init_db()
    logger.info(f"🚀 Starting Smart Attendance on port {FLASK_PORT}")
    app.run(debug=FLASK_DEBUG, port=FLASK_PORT)
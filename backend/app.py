from flask import Flask
from flask_cors import CORS
from backend.models import init_db, Session, Attendance, Student
from backend.routes.enroll import enroll_bp
from backend.routes.attend import attend_bp
from backend.routes.reports import reports_bp
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date

app = Flask(__name__)
CORS(app)

app.register_blueprint(enroll_bp)
app.register_blueprint(attend_bp)
app.register_blueprint(reports_bp)

def auto_mark_absent():
    session = Session()
    students    = session.query(Student).all()
    present_ids = {a.student_id for a in
                   session.query(Attendance).filter_by(date=date.today(), status="present").all()}
    for s in students:
        if s.id not in present_ids:
            rec_id = f"{s.id}_{date.today()}"
            session.merge(Attendance(id=rec_id, student_id=s.id, date=date.today(), status="absent"))
    session.commit()
    session.close()
    print(f"Auto-marked absents for {date.today()}")

scheduler = BackgroundScheduler()
scheduler.add_job(auto_mark_absent, "cron", hour=10, minute=0)
scheduler.start()

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
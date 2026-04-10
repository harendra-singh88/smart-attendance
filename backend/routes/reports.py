from flask import Blueprint, jsonify, request, send_file
from backend.models import Session, Attendance, Student
from datetime import date
import pandas as pd, io

reports_bp = Blueprint("reports", __name__)

@reports_bp.route("/api/report/today", methods=["GET"])
def today_report():
    session = Session()
    records = session.query(Attendance, Student)\
        .join(Student, Attendance.student_id == Student.id)\
        .filter(Attendance.date == date.today()).all()
    session.close()

    data = [{"student_id": a.student_id, "name": s.name,
             "status": a.status, "time": str(a.timestamp)} for a, s in records]
    return jsonify(data)

@reports_bp.route("/api/report/export", methods=["GET"])
def export_csv():
    session = Session()
    records = session.query(Attendance, Student)\
        .join(Student, Attendance.student_id == Student.id).all()
    session.close()

    df = pd.DataFrame([{"ID": a.student_id, "Name": s.name, "Date": a.date,
                         "Status": a.status, "Time": a.timestamp} for a, s in records])
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return send_file(buf, mimetype="text/csv", download_name="attendance.csv", as_attachment=True)
@reports_bp.route("/api/students", methods=["GET"])
def get_students():
    session = Session()
    students = session.query(Student).all()
    session.close()
    return jsonify([{
        "id": s.id,
        "name": s.name,
        "class_": s.class_,
        "enrolled": str(s.enrolled)
    } for s in students])
@reports_bp.route("/api/report/date", methods=["GET"])
def date_report():
    from datetime import datetime
    date_str = request.args.get("date")
    try:
        filter_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except:
        return jsonify({"error": "Invalid date format"}), 400

    session = Session()
    records = session.query(Attendance, Student)\
        .join(Student, Attendance.student_id == Student.id)\
        .filter(Attendance.date == filter_date).all()
    session.close()

    return jsonify([{
        "student_id": a.student_id,
        "name": s.name,
        "date": str(a.date),
        "status": a.status,
        "time": str(a.timestamp)
    } for a, s in records])
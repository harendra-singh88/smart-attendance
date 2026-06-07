import io
import logging
import pandas as pd
from flask import Blueprint, jsonify, request, send_file
from datetime import date, datetime
from backend.models import Session, Attendance, Student

logger     = logging.getLogger(__name__)
reports_bp = Blueprint("reports", __name__)


@reports_bp.route("/api/report/today", methods=["GET"])
def today_report():
    session = Session()
    try:
        records = (
            session.query(Attendance, Student)
            .join(Student, Attendance.student_id == Student.id)
            .filter(Attendance.date == date.today())
            .all()
        )
        data = [
            {
                "student_id": a.student_id,
                "name":       s.name,
                "status":     a.status,
                "time":       a.timestamp.isoformat() if a.timestamp else None
            }
            for a, s in records
        ]
        return jsonify(data)
    except Exception as e:
        logger.error(f"❌ today_report error: {e}")
        return jsonify({"error": "Could not fetch today's report"}), 500
    finally:
        session.close()


@reports_bp.route("/api/report/date", methods=["GET"])
def date_report():
    date_str = request.args.get("date", "")
    try:
        filter_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    session = Session()
    try:
        records = (
            session.query(Attendance, Student)
            .join(Student, Attendance.student_id == Student.id)
            .filter(Attendance.date == filter_date)
            .all()
        )
        data = [
            {
                "student_id": a.student_id,
                "name":       s.name,
                "date":       str(a.date),
                "status":     a.status,
                "time":       a.timestamp.isoformat() if a.timestamp else None
            }
            for a, s in records
        ]
        return jsonify(data)
    except Exception as e:
        logger.error(f"❌ date_report error: {e}")
        return jsonify({"error": "Could not fetch report"}), 500
    finally:
        session.close()


@reports_bp.route("/api/students", methods=["GET"])
def get_students():
    session = Session()
    try:
        students = session.query(Student).all()
        return jsonify([
            {
                "id":       s.id,
                "name":     s.name,
                "class_":   s.class_,
                "enrolled": s.enrolled.isoformat() if s.enrolled else None
            }
            for s in students
        ])
    except Exception as e:
        logger.error(f"❌ get_students error: {e}")
        return jsonify({"error": "Could not fetch students"}), 500
    finally:
        session.close()


@reports_bp.route("/api/report/export", methods=["GET"])
def export_csv():
    session = Session()
    try:
        records = (
            session.query(Attendance, Student)
            .join(Student, Attendance.student_id == Student.id)
            .all()
        )
        rows = [
            {
                "ID":     a.student_id,
                "Name":   s.name,
                "Class":  s.class_,
                "Date":   str(a.date),
                "Status": a.status,
                "Time":   str(a.timestamp) if a.timestamp else ""
            }
            for a, s in records
        ]
        df  = pd.DataFrame(rows)
        buf = io.BytesIO()
        df.to_csv(buf, index=False)
        buf.seek(0)
        return send_file(buf, mimetype="text/csv", download_name="attendance.csv", as_attachment=True)
    except Exception as e:
        logger.error(f"❌ export_csv error: {e}")
        return jsonify({"error": "Could not export CSV"}), 500
    finally:
        session.close()
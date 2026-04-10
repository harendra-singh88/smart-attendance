import uuid, os
from flask import Blueprint, request, jsonify
from datetime import datetime, date
from backend.face_engine import recognize
from backend.models import Session, Attendance

attend_bp = Blueprint("attend", __name__)
WINDOW_START = 7   # 7 AM
WINDOW_END   = 10  # 10 AM

@attend_bp.route("/api/attend", methods=["POST"])
def check_in():
    now = datetime.now()

    if not (WINDOW_START <= now.hour < WINDOW_END):
        return jsonify({"error": f"Check-in only allowed between {WINDOW_START}AM-{WINDOW_END}AM"}), 403

    photo = request.files.get("photo")
    if not photo:
        return jsonify({"error": "No photo uploaded"}), 400

    temp_path = f"temp_{uuid.uuid4().hex}.jpg"
    photo.save(temp_path)

    try:
        student_id, dist = recognize(temp_path)
        if not student_id:
            return jsonify({"status": "unknown", "message": "Face not recognized"}), 200

        session = Session()
        record_id = f"{student_id}_{date.today()}"
        existing = session.get(Attendance, record_id)

        if existing and existing.status == "present":
            session.close()
            return jsonify({"status": "already_marked", "student_id": student_id})

        record = existing or Attendance(id=record_id, student_id=student_id, date=date.today())
        record.status    = "present"
        record.timestamp = now
        session.merge(record)
        session.commit()
        session.close()

        return jsonify({"status": "present", "student_id": student_id, "distance": round(dist, 2)})
    finally:
        os.remove(temp_path)
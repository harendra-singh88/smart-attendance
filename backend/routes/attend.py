import uuid
import os
import logging
from flask import Blueprint, request, jsonify
from datetime import datetime, date
from backend.face_engine import recognize
from backend.models import Session, Attendance
from backend.config import WINDOW_START, WINDOW_END

logger    = logging.getLogger(__name__)
attend_bp = Blueprint("attend", __name__)


@attend_bp.route("/api/attend", methods=["POST"])
def check_in():
    now = datetime.now()

    # Enforce check-in time window
    if not (WINDOW_START <= now.hour < WINDOW_END):
        return jsonify({
            "error": f"Check-in only allowed between {WINDOW_START}:00 AM and {WINDOW_END}:00 AM"
        }), 403

    photo = request.files.get("photo")
    if not photo:
        return jsonify({"error": "No photo uploaded"}), 400

    # Save temp file
    temp_path = f"temp_{uuid.uuid4().hex}.jpg"
    photo.save(temp_path)

    try:
        student_id, dist = recognize(temp_path)

        # Face not recognized
        if not student_id:
            return jsonify({"status": "unknown", "message": "Face not recognized"}), 200

        session = Session()
        today   = date.today()

        # Check if already marked present
        existing = session.get(Attendance, (student_id, today))
        if existing and existing.status == "present":
            session.close()
            return jsonify({
                "status":     "already_marked",
                "student_id": student_id
            })

        # Mark present
        if existing:
            existing.status    = "present"
            existing.timestamp = now
        else:
            session.add(Attendance(
                student_id = student_id,
                date       = today,
                status     = "present",
                timestamp  = now
            ))

        session.commit()
        session.close()

        # Fix: safely serialize distance (inf is not valid JSON)
        safe_dist = round(dist, 2) if dist != float("inf") else None

        logger.info(f"✅ {student_id} marked present at {now.strftime('%H:%M:%S')}")
        return jsonify({
            "status":     "present",
            "student_id": student_id,
            "distance":   safe_dist
        })

    except Exception as e:
        logger.error(f"❌ check_in error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
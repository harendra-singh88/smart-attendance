import os
import uuid
import logging
from flask import Blueprint, request, jsonify
from backend.face_engine import enroll
from backend.models import Session, Student

logger    = logging.getLogger(__name__)
enroll_bp = Blueprint("enroll", __name__)


@enroll_bp.route("/api/enroll", methods=["POST"])
def enroll_student():
    student_id = request.form.get("student_id", "").strip()
    name       = request.form.get("name", "").strip()
    class_     = request.form.get("class_", "").strip()
    images     = request.files.getlist("photos")

    # Validate required fields
    if not student_id or not name:
        return jsonify({"error": "student_id and name are required"}), 400

    if len(images) < 3:
        return jsonify({"error": "Please upload at least 3 face photos"}), 400

    # Validate student_id — no spaces or special chars
    if not student_id.replace("-", "").replace("_", "").isalnum():
        return jsonify({"error": "student_id must be alphanumeric (hyphens/underscores allowed)"}), 400

    # Save uploaded images temporarily
    temp_paths = []
    for img in images:
        path = f"temp_{uuid.uuid4().hex}.jpg"
        img.save(path)
        temp_paths.append(path)

    try:
        count = enroll(student_id, temp_paths)

        # Save student to DB if not already enrolled
        session = Session()
        if not session.get(Student, student_id):
            session.add(Student(id=student_id, name=name, class_=class_))
            session.commit()
            logger.info(f"✅ New student added: {student_id} — {name}")
        else:
            logger.info(f"ℹ️ Re-enrolled existing student: {student_id}")
        session.close()

        return jsonify({"message": f"Enrolled {name} with {count} face samples."})

    except ValueError as e:
        return jsonify({"error": str(e)}), 422

    except Exception as e:
        logger.error(f"❌ Enrollment error: {e}")
        return jsonify({"error": "Internal server error"}), 500

    finally:
        for p in temp_paths:
            if os.path.exists(p):
                os.remove(p)
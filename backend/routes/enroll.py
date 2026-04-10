import os, uuid
from flask import Blueprint, request, jsonify
from backend.face_engine import enroll
from backend.models import Session, Student

enroll_bp = Blueprint("enroll", __name__)

@enroll_bp.route("/api/enroll", methods=["POST"])
def enroll_student():
    student_id = request.form.get("student_id")
    name       = request.form.get("name")
    class_     = request.form.get("class_", "")
    images     = request.files.getlist("photos")  # 5-20 photos

    if not student_id or not name or not images:
        return jsonify({"error": "student_id, name and photos are required"}), 400

    # Save uploaded images temporarily
    temp_paths = []
    for img in images:
        path = f"temp_{uuid.uuid4().hex}.jpg"
        img.save(path)
        temp_paths.append(path)

    try:
        count = enroll(student_id, temp_paths)
        # Save student to DB
        session = Session()
        if not session.get(Student, student_id):
            session.add(Student(id=student_id, name=name, class_=class_))
            session.commit()
        session.close()
        return jsonify({"message": f"Enrolled {name} with {count} face samples."})
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    finally:
        for p in temp_paths:
            os.remove(p)
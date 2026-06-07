import os
import pickle
import logging
import numpy as np
from deepface import DeepFace
from backend.config import EMBED_DIR, MODEL_NAME, THRESHOLD

logger = logging.getLogger(__name__)

os.makedirs(EMBED_DIR, exist_ok=True)


def enroll(student_id: str, image_paths: list[str]) -> int:
    """
    Generate and store face embeddings for a student.
    Requires at least 3 valid face images.
    """
    embeddings = []

    for path in image_paths:
        try:
            result = DeepFace.represent(path, model_name=MODEL_NAME, enforce_detection=True)
            embeddings.append(result[0]["embedding"])
            logger.info(f"✅ Processed: {path}")
        except Exception as e:
            logger.warning(f"⚠️ Skipping {path}: {e}")

    if len(embeddings) < 3:
        raise ValueError(f"Only {len(embeddings)} valid face(s) found. Need at least 3.")

    embed_path = os.path.join(EMBED_DIR, f"{student_id}.pkl")
    with open(embed_path, "wb") as f:
        pickle.dump(embeddings, f)

    logger.info(f"✅ Enrolled {student_id} with {len(embeddings)} embeddings")
    return len(embeddings)


def recognize(image_path: str) -> tuple[str | None, float]:
    """
    Compare a captured photo against all enrolled students.
    Returns (student_id, distance) or (None, inf) if not recognized.
    """
    try:
        query = DeepFace.represent(image_path, model_name=MODEL_NAME, enforce_detection=True)
        query_emb = np.array(query[0]["embedding"])
    except Exception as e:
        logger.warning(f"⚠️ Could not extract face from image: {e}")
        return None, float("inf")

    best_id   = None
    best_dist = float("inf")

    for pkl_file in os.listdir(EMBED_DIR):
        if not pkl_file.endswith(".pkl"):
            continue

        student_id = pkl_file[:-4]
        embed_path = os.path.join(EMBED_DIR, pkl_file)

        try:
            with open(embed_path, "rb") as f:
                stored = pickle.load(f)

            distances = [np.linalg.norm(query_emb - np.array(e)) for e in stored]
            dist = min(distances)

            if dist < best_dist:
                best_dist = dist
                best_id   = student_id

        except Exception as e:
            logger.error(f"❌ Error reading embeddings for {student_id}: {e}")
            continue

    if best_dist < THRESHOLD:
        logger.info(f"✅ Recognized: {best_id} (distance: {best_dist:.2f})")
        return best_id, best_dist

    logger.warning(f"⚠️ No match found (best distance: {best_dist:.2f})")
    return None, best_dist
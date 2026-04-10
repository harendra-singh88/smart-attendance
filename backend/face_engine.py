import os, pickle
import numpy as np
from deepface import DeepFace

EMBED_DIR  = "backend/embeddings"
MODEL      = "Facenet"
THRESHOLD  = 18.0   # Euclidean distance threshold (tune as needed)

os.makedirs(EMBED_DIR, exist_ok=True)

def enroll(student_id: str, image_paths: list[str]) -> int:
    """Generate and store face embeddings for a student."""
    embeddings = []
    for path in image_paths:
        try:
            result = DeepFace.represent(path, model_name=MODEL, enforce_detection=True)
            embeddings.append(result[0]["embedding"])
        except Exception as e:
            print(f"Skipping {path}: {e}")

    if not embeddings:
        raise ValueError("No valid faces found in provided images.")

    with open(f"{EMBED_DIR}/{student_id}.pkl", "wb") as f:
        pickle.dump(embeddings, f)

    return len(embeddings)


def recognize(image_path: str) -> tuple[str | None, float]:
    """Compare a captured photo against all enrolled students."""
    try:
        query = DeepFace.represent(image_path, model_name=MODEL, enforce_detection=True)
        query_emb = np.array(query[0]["embedding"])
    except Exception:
        return None, float("inf")

    best_id, best_dist = None, float("inf")

    for pkl_file in os.listdir(EMBED_DIR):
        if not pkl_file.endswith(".pkl"):
            continue
        student_id = pkl_file[:-4]
        with open(f"{EMBED_DIR}/{pkl_file}", "rb") as f:
            stored = pickle.load(f)

        distances = [np.linalg.norm(query_emb - np.array(e)) for e in stored]
        dist = min(distances)

        if dist < best_dist:
            best_dist = dist
            best_id = student_id

    if best_dist < THRESHOLD:
        return best_id, best_dist
    return None, best_dist
import os
from dotenv import load_dotenv

load_dotenv()

# Flask
FLASK_PORT  = int(os.getenv("FLASK_PORT", 5000))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

# Face Recognition
EMBED_DIR   = os.getenv("EMBED_DIR", "backend/embeddings")
MODEL_NAME  = os.getenv("MODEL_NAME", "Facenet")
THRESHOLD   = float(os.getenv("THRESHOLD", 18.0))

# Attendance window
WINDOW_START = int(os.getenv("WINDOW_START", 7))
WINDOW_END   = int(os.getenv("WINDOW_END", 10))

# Scheduler
ABSENT_HOUR   = int(os.getenv("ABSENT_HOUR", 10))
ABSENT_MINUTE = int(os.getenv("ABSENT_MINUTE", 5))
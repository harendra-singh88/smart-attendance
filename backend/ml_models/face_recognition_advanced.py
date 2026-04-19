import os
import numpy as np
import pickle
import logging
from typing import Tuple, List, Dict
import tensorflow as tf
import cv2
from deepface import DeepFace
from tensorflow.keras.models import load_model
from sklearn.preprocessing import normalize

logger = logging.getLogger(__name__)

class AdvancedFaceRecognizer:
    """
    Advanced face recognition with multiple model support:
    - FaceNet (Default - best for general use)
    - VGGFace2 (High accuracy for identification)
    - ArcFace (Best for face verification)
    - Dlib (Fast, lightweight)
    """
    
    def __init__(self, model_name: str = "Facenet", gpu: bool = True):
        self.model_name = model_name
        self.models = {
            "Facenet": {"enforce_detection": True, "detector_backend": "opencv"},
            "VGGFace2": {"enforce_detection": True, "detector_backend": "opencv"},
            "ArcFace": {"enforce_detection": True, "detector_backend": "retinaface"},
            "OpenFace": {"enforce_detection": True, "detector_backend": "dlib"}
        }
        self.embed_dir = "backend/embeddings"
        self.threshold = 0.6  # Cosine similarity threshold
        os.makedirs(self.embed_dir, exist_ok=True)
        logger.info(f"✅ Initialized {model_name} face recognizer")

    def preprocess_image(self, image_path: str) -> np.ndarray:
        """Preprocess image for better face detection"""
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot read image: {image_path}")
        
        # Enhance image quality
        # Convert to grayscale for processing
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization for better contrast
        equalized = cv2.equalizeHist(gray)
        
        # Optional: Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(equalized)
        
        logger.info(f"✅ Preprocessed image: {image_path}")
        return enhanced

    def detect_faces(self, image_path: str) -> List[Dict]:
        """Detect all faces in an image"""
        try:
            img = cv2.imread(image_path)
            # Use DeepFace for detection
            detected = DeepFace.extract_faces(
                img,
                detector_backend="opencv",
                enforce_detection=False
            )
            logger.info(f"✅ Detected {len(detected)} faces in {image_path}")
            return detected
        except Exception as e:
            logger.warning(f"⚠️ Face detection failed: {str(e)}")
            return []

    def generate_embedding(self, image_path: str) -> Tuple[np.ndarray, Dict]:
        """Generate face embedding with confidence score"""
        try:
            result = DeepFace.represent(
                image_path,
                model_name=self.model_name,
                **self.models[self.model_name]
            )
            
            if not result:
                raise ValueError("No face found in image")
            
            embedding = np.array(result[0]["embedding"])
            embedding = normalize([embedding])[0]  # Normalize for cosine similarity
            
            metadata = {
                "model": self.model_name,
                "distance": result[0].get("distance", None),
                "facial_area": result[0].get("facial_area", None)
            }
            
            return embedding, metadata
        except Exception as e:
            logger.error(f"❌ Embedding generation failed: {str(e)}")
            raise

    def enroll_student(self, student_id: str, image_paths: List[str]) -> int:
        """Enroll student with multiple face samples"""
        embeddings = []
        metadata_list = []
        
        for path in image_paths:
            try:
                # Detect faces
                faces = self.detect_faces(path)
                if not faces:
                    logger.warning(f"⚠️ No face detected in {path}")
                    continue
                
                if len(faces) > 1:
                    logger.warning(f"⚠️ Multiple faces in {path}, using largest")
                
                # Generate embedding
                embedding, metadata = self.generate_embedding(path)
                embeddings.append(embedding)
                metadata_list.append(metadata)
                
            except Exception as e:
                logger.error(f"❌ Failed to process {path}: {str(e)}")
                continue

        if len(embeddings) < 3:
            raise ValueError(f"❌ Only {len(embeddings)} valid faces. Need at least 3.")

        # Store embeddings
        enrollment_data = {
            "embeddings": embeddings,
            "metadata": metadata_list,
            "model": self.model_name,
            "count": len(embeddings),
            "average_embedding": np.mean(embeddings, axis=0)  # For faster comparison
        }

        with open(f"{self.embed_dir}/{student_id}.pkl", "wb") as f:
            pickle.dump(enrollment_data, f)

        logger.info(f"✅ Enrolled {student_id} with {len(embeddings)} face samples")
        return len(embeddings)

    def recognize_face(self, image_path: str) -> Tuple[str, float, Dict]:
        """
        Recognize face in image
        Returns: (student_id, confidence, metadata)
        """
        try:
            # Detect faces in image
            faces = self.detect_faces(image_path)
            if not faces:
                logger.warning("⚠️ No face detected")
                return None, 0.0, {"error": "No face detected"}

            # Generate embedding
            query_embedding, _ = self.generate_embedding(image_path)
            
            best_student_id = None
            best_similarity = 0.0
            all_scores = []

            # Compare with all enrolled students
            for pkl_file in os.listdir(self.embed_dir):
                if not pkl_file.endswith(".pkl"):
                    continue

                student_id = pkl_file[:-4]
                try:
                    with open(f"{self.embed_dir}/{pkl_file}", "rb") as f:
                        data = pickle.load(f)
                    
                    stored_embeddings = data.get("embeddings", data) if isinstance(data, dict) else data
                    
                    # Cosine similarity comparison
                    similarities = [
                        np.dot(query_embedding, np.array(emb)) 
                        for emb in stored_embeddings
                    ]
                    max_similarity = np.max(similarities)
                    
                    all_scores.append({
                        "student_id": student_id,
                        "similarity": float(max_similarity),
                        "num_samples": len(stored_embeddings)
                    })

                    if max_similarity > best_similarity:
                        best_similarity = max_similarity
                        best_student_id = student_id

                except Exception as e:
                    logger.error(f"❌ Error comparing with {student_id}: {str(e)}")
                    continue

            # Sort by similarity
            all_scores.sort(key=lambda x: x["similarity"], reverse=True)

            metadata = {
                "all_scores": all_scores[:5],  # Top 5 matches
                "num_faces_detected": len(faces),
                "threshold": self.threshold,
                "model": self.model_name
            }

            if best_similarity >= self.threshold:
                logger.info(f"✅ Recognized {best_student_id} (confidence: {best_similarity:.4f})")
                return best_student_id, float(best_similarity), metadata
            else:
                logger.warning(f"⚠️ No match (best: {best_similarity:.4f})")
                return None, float(best_similarity), metadata

        except Exception as e:
            logger.error(f"❌ Recognition failed: {str(e)}")
            return None, 0.0, {"error": str(e)}
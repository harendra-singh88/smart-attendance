import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models # type: ignore
from tensorflow.keras.applications import VGG16, ResNet50, InceptionV3 # type: ignore
from sklearn.model_selection import train_test_split # type: ignore
from sklearn.preprocessing import StandardScaler # type: ignore
import pickle
import os

class FaceEmbeddingModel:
    """
    Custom deep learning model for face embeddings
    using transfer learning with pre-trained architectures
    """
    
    def __init__(self, base_model_name: str = "ResNet50"):
        self.base_model_name = base_model_name
        self.embedding_dim = 128
        self.build_model()

    def build_model(self):
        """Build deep learning model for face embeddings"""
        
        # Load pre-trained base model
        if self.base_model_name == "ResNet50":
            base_model = ResNet50(weights='imagenet', include_top=False)
        elif self.base_model_name == "VGG16":
            base_model = VGG16(weights='imagenet', include_top=False)
        else:
            base_model = InceptionV3(weights='imagenet', include_top=False)

        # Freeze base model weights
        base_model.trainable = False

        # Build custom embedding head
        model = models.Sequential([
            layers.Input(shape=(224, 224, 3)),
            base_model,
            layers.GlobalAveragePooling2D(),
            layers.Dense(512, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.5),
            layers.Dense(256, activation='relu'),
            layers.BatchNormalization(),
            layers.Dropout(0.3),
            layers.Dense(self.embedding_dim, activation='relu'),  # Embedding layer
            layers.Lambda(lambda x: tf.keras.backend.l2_normalize(x, axis=1))  # L2 normalization
        ])

        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
            loss='cosine_similarity',
            metrics=['accuracy']
        )

        self.model = model
        print(f"✅ Built {self.base_model_name} embedding model")

    def train(self, X_train, y_train, epochs=50, batch_size=32):
        """Train the embedding model"""
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=1
        )
        return history

    def generate_embeddings(self, images):
        """Generate embeddings for images"""
        return self.model.predict(images)

    def save_model(self, path):
        """Save trained model"""
        self.model.save(path)
        print(f"✅ Model saved to {path}")

    def load_model(self, path):
        """Load trained model"""
        self.model = tf.keras.models.load_model(path)
        print(f"✅ Model loaded from {path}")
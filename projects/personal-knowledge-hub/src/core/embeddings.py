"""
Embedding model management for Personal Knowledge Hub.
Handles both local and API-based embedding generation.
"""

import os
import logging
from typing import List, Union, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingManager:
    """Manages embedding generation using local models or APIs."""
    
    def __init__(self, config_path: str = "config/settings.yaml"):
        """Initialize the embedding manager with configuration."""
        self.config = self._load_config(config_path)
        self.embedding_type = self.config["embedding"]["type"]
        
        # Initialize appropriate embedding model based on config
        if self.embedding_type == "local":
            self.model_name = self.config["embedding"]["local_model"]
            self.dimensions = self.config["embedding"]["local_dimensions"]
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Initialized local embedding model: {self.model_name}")
        elif self.embedding_type == "api":
            self.model_name = self.config["embedding"]["api_model"]
            self.dimensions = self.config["embedding"]["api_dimensions"]
            self.api_key = os.environ.get("EMBEDDING_API_KEY") or self.config["embedding"]["api_key"]
            if not self.api_key:
                raise ValueError("API key required for API-based embeddings")
            logger.info(f"Initialized API embedding model: {self.model_name}")
        else:
            raise ValueError(f"Unsupported embedding type: {self.embedding_type}")
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors (each vector is a list of floats)
        """
        if self.embedding_type == "local":
            return self._embed_local(texts)
        elif self.embedding_type == "api":
            return self._embed_api(texts)
        else:
            raise ValueError(f"Unsupported embedding type: {self.embedding_type}")
    
    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using local model."""
        # Handle empty texts
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text.strip())
                valid_indices.append(i)
        
        if not valid_texts:
            # Return zero vectors for all inputs
            return [[0.0] * self.dimensions for _ in texts]
        
        # Generate embeddings for valid texts
        embeddings = self.model.encode(valid_texts, convert_to_numpy=True)
        
        # Ensure embeddings are 2D array
        if len(embeddings.shape) == 1:
            embeddings = embeddings.reshape(1, -1)
        
        # Create result list with proper ordering
        result = [[0.0] * self.dimensions for _ in texts]
        for i, embedding in zip(valid_indices, embeddings):
            result[i] = embedding.tolist()
        
        return result
    
    def _embed_api(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using API (placeholder implementation)."""
        # This is a placeholder - actual implementation would depend on the API provider
        # For now, we'll use the local model as a fallback
        logger.warning("API embedding not implemented yet, using local model as fallback")
        return self._embed_local(texts)
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors."""
        return self.dimensions
    
    def similarity_score(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)
        
        # Handle zero vectors
        if np.all(vec1 == 0) or np.all(vec2 == 0):
            return 0.0
        
        # Calculate cosine similarity
        similarity = np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
        return float(similarity)
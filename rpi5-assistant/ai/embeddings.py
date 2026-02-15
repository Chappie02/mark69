"""
Embeddings model for RAG
Lightweight model efficient for 4GB RAM
"""

import logging
from typing import List, Optional

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logging.warning("sentence-transformers not available - embeddings simulation mode")

from config import RAG_EMBEDDING_MODEL

logger = logging.getLogger(__name__)

# =============================================
# EMBEDDINGS MODEL
# =============================================
class EmbeddingsModel:
    """Generates embeddings for RAG system"""
    
    def __init__(self):
        """Initialize embeddings model"""
        self.model: Optional[object] = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            self._load_model()
        else:
            logger.warning("sentence-transformers not available - embeddings will not work")
    
    def _load_model(self) -> None:
        """Load embeddings model"""
        try:
            logger.info(f"Loading embeddings model: {RAG_EMBEDDING_MODEL}...")
            self.model = SentenceTransformer(RAG_EMBEDDING_MODEL)
            logger.info(f"✓ Embeddings model loaded: {RAG_EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load embeddings model: {e}")
            self.model = None
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None
        """
        try:
            if not self.model:
                logger.warning("Embeddings model not loaded")
                return None
            
            # Generate embedding
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return None
    
    def embed_texts(self, texts: List[str]) -> Optional[List[List[float]]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts
            
        Returns:
            List of embedding vectors
        """
        try:
            if not self.model:
                logger.warning("Embeddings model not loaded")
                return None
            
            # Generate embeddings
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return [emb.tolist() for emb in embeddings]
            
        except Exception as e:
            logger.error(f"Batch embedding failed: {e}")
            return None
    
    def cleanup(self) -> None:
        """Cleanup model"""
        if self.model:
            try:
                self.model = None
                logger.info("✓ Embeddings model unloaded")
            except Exception as e:
                logger.error(f"Embeddings cleanup failed: {e}")

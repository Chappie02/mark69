"""
RAG (Retrieval-Augmented Generation) using ChromaDB
Persistent memory system
"""

import logging
from typing import Optional, List
import os

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    logging.warning("chromadb not available - RAG simulation mode")

from config import (
    RAG_COLLECTION_NAME, RAG_SIMILARITY_THRESHOLD, RAG_TOP_K,
    VECTORDB_DIR
)
from ai.embeddings import EmbeddingsModel

logger = logging.getLogger(__name__)

# =============================================
# RAG MEMORY
# =============================================
class RAGMemory:
    """RAG system using ChromaDB for persistent memory"""
    
    def __init__(self, embeddings: EmbeddingsModel):
        """
        Initialize RAG system
        
        Args:
            embeddings: EmbeddingsModel instance
        """
        self.embeddings = embeddings
        self.client: Optional[object] = None
        self.collection: Optional[object] = None
        
        if CHROMADB_AVAILABLE:
            self._init_chromadb()
        else:
            logger.warning("chromadb not available - RAG will not work")
    
    def _init_chromadb(self) -> None:
        """Initialize ChromaDB client and collection"""
        try:
            logger.info(f"Initializing ChromaDB at {VECTORDB_DIR}...")
            
            # Create persistent client
            self.client = chromadb.PersistentClient(
                path=str(VECTORDB_DIR),
                anonymized_telemetry=False
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=RAG_COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info(f"✓ ChromaDB initialized: {RAG_COLLECTION_NAME}")
            
            # Log stats
            count = self.collection.count()
            logger.info(f"  Existing documents: {count}")
            
        except Exception as e:
            logger.error(f"ChromaDB initialization failed: {e}")
            self.client = None
            self.collection = None
    
    def store(self, text: str, metadata: Optional[dict] = None) -> bool:
        """
        Store text in RAG memory
        
        Args:
            text: Text to store
            metadata: Optional metadata dict
            
        Returns:
            True if successful
        """
        try:
            if not self.collection:
                logger.warning("ChromaDB not initialized")
                return False
            
            # Generate embedding
            embedding = self.embeddings.embed_text(text)
            if not embedding:
                logger.error("Failed to generate embedding")
                return False
            
            # Generate unique ID
            doc_id = f"doc_{self.collection.count()}"
            
            # Store in ChromaDB
            self.collection.add(
                ids=[doc_id],
                documents=[text],
                embeddings=[embedding],
                metadatas=[metadata or {}]
            )
            
            logger.info(f"Stored in RAG: {text[:50]}...")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store in RAG: {e}")
            return False
    
    def query(self, query_text: str, top_k: int = RAG_TOP_K) -> str:
        """
        Query RAG memory for relevant context
        
        Args:
            query_text: Query text
            top_k: Number of results to retrieve
            
        Returns:
            Formatted context string
        """
        try:
            if not self.collection:
                logger.warning("ChromaDB not initialized")
                return ""
            
            # Generate query embedding
            query_embedding = self.embeddings.embed_text(query_text)
            if not query_embedding:
                logger.warning("Failed to generate query embedding")
                return ""
            
            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={"$gte": {"distance": RAG_SIMILARITY_THRESHOLD}}  # Similarity threshold
            )
            
            # Format results
            context = ""
            if results and results["documents"] and results["documents"][0]:
                logger.info(f"RAG retrieved {len(results['documents'][0])} results")
                for i, doc in enumerate(results["documents"][0]):
                    distance = results["distances"][0][i] if "distances" in results else 0
                    context += f"[{i+1}] {doc}\n"
            else:
                logger.info("No relevant results in RAG")
            
            return context.strip()
            
        except Exception as e:
            logger.error(f"RAG query failed: {e}", exc_info=True)
            return ""
    
    def get_stats(self) -> dict:
        """Get RAG collection statistics"""
        try:
            if not self.collection:
                return {"status": "not_initialized"}
            
            return {
                "status": "ready",
                "documents": self.collection.count(),
                "collection": RAG_COLLECTION_NAME
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"status": "error"}
    
    def cleanup(self) -> None:
        """Cleanup RAG"""
        try:
            if self.client:
                # ChromaDB auto-persists, just close client
                self.client = None
                logger.info("✓ RAG cleaned up")
        except Exception as e:
            logger.error(f"RAG cleanup failed: {e}")

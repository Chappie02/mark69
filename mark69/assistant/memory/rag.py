"""
RAG memory using ChromaDB.
Stores conversation history and object locations for queries like "Where is my bottle?"
"""

import logging
from typing import List, Optional

from assistant.config import (
    CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_CONV,
    CHROMA_COLLECTION_OBJECTS,
)

logger = logging.getLogger(__name__)


class RAGMemory:
    """ChromaDB-backed memory for conversations and object detections."""

    def __init__(self) -> None:
        self._client = None
        self._conv_collection = None
        self._objects_collection = None
        self._embed_fn = None
        self._initialized = False

    def init(self) -> bool:
        """Initialize ChromaDB and collections. Returns True on success."""
        try:
            import chromadb
            from chromadb.config import Settings
            from chromadb.utils import embedding_functions

            self._client = chromadb.PersistentClient(
                path=CHROMA_PERSIST_DIR,
                settings=Settings(anonymized_telemetry=False),
            )
            # Pi-friendly small model for embeddings
            ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2"
            )
            self._conv_collection = self._client.get_or_create_collection(
                CHROMA_COLLECTION_CONV,
                embedding_function=ef,
                metadata={"description": "Conversation turns"},
            )
            self._objects_collection = self._client.get_or_create_collection(
                CHROMA_COLLECTION_OBJECTS,
                embedding_function=ef,
                metadata={"description": "Detected object locations"},
            )
            self._initialized = True
            logger.info("ChromaDB RAG initialized: %s", CHROMA_PERSIST_DIR)
            return True
        except Exception as e:
            logger.exception("ChromaDB init failed: %s", e)
            self._initialized = False
            return False

    def add_conversation(self, user_text: str, assistant_text: str) -> None:
        """Store one conversation turn for RAG."""
        if not self._initialized:
            return
        try:
            doc = f"User: {user_text}\nAssistant: {assistant_text}"
            self._conv_collection.add(
                documents=[doc],
                ids=[f"conv_{id(self)}_{len(doc)}"],
                metadatas=[{"user": user_text[:200], "assistant": assistant_text[:200]}],
            )
        except Exception as e:
            logger.debug("Add conversation failed: %s", e)

    def add_object_location(self, labels: List[str], image_path: str, context: str = "") -> None:
        """Store detected objects and location (e.g. image path / description)."""
        if not self._initialized:
            return
        try:
            doc = f"Objects: {', '.join(labels)}. Location: {image_path}. {context}".strip()
            self._objects_collection.add(
                documents=[doc],
                ids=[f"obj_{hash(doc) % 10**10}"],
                metadatas=[{"labels": ",".join(labels), "image": image_path}],
            )
        except Exception as e:
            logger.debug("Add object location failed: %s", e)

    def query(self, question: str, collection: Optional[str] = None, n_results: int = 3) -> List[str]:
        """
        RAG query. Returns list of relevant document snippets.
        collection: "conversations" | "object_locations" | None (both).
        """
        if not self._initialized:
            return []
        try:
            results = []
            if collection is None or collection == "conversations":
                r = self._conv_collection.query(query_texts=[question], n_results=n_results)
                if r and r["documents"]:
                    results.extend(r["documents"][0] or [])
            if collection is None or collection == "object_locations":
                r = self._objects_collection.query(query_texts=[question], n_results=n_results)
                if r and r["documents"]:
                    results.extend(r["documents"][0] or [])
            return results
        except Exception as e:
            logger.exception("RAG query failed: %s", e)
            return []

    def get_context_for_question(self, question: str, max_chars: int = 1500) -> str:
        """Get concatenated context string for LLM (e.g. for 'Where is my bottle?')."""
        docs = self.query(question, collection=None, n_results=5)
        if not docs:
            return ""
        context = "\n".join(docs)
        if len(context) > max_chars:
            context = context[: max_chars - 3] + "..."
        return context

    def cleanup(self) -> None:
        self._client = None
        self._conv_collection = None
        self._objects_collection = None
        self._initialized = False
        logger.info("RAG cleanup done")

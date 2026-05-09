"""
ChromaDB Client — shared by AI Developer 1 (RAG pipeline) and AI Developer 2 (/query endpoint).
Provides persistent vector storage for regulatory filing knowledge base.
"""

import os
import importlib
import logging
import math
import re
from collections import Counter
from typing import Any

try:
    chromadb: Any = importlib.import_module("chromadb")
    Settings: Any = getattr(importlib.import_module("chromadb.config"), "Settings")
    SentenceTransformer: Any = getattr(
        importlib.import_module("sentence_transformers"),
        "SentenceTransformer",
    )
except Exception as exc:
    chromadb = None
    Settings = None
    SentenceTransformer = None
    CHROMA_IMPORT_ERROR = exc
else:
    CHROMA_IMPORT_ERROR = None

logger = logging.getLogger(__name__)

COLLECTION_NAME = "regulatory_filings_kb"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
CHROMA_PATH = os.getenv("CHROMA_DATA_PATH", "./chroma_data")

DEFAULT_KB_DOCUMENTS = [
    {
        "id": "quarterly-filing-deadline",
        "text": "Quarterly regulatory filings are generally due within 45 days after the end of the quarter unless the regulator specifies a shorter deadline.",
        "metadata": {"source": "Default regulatory knowledge base", "topic": "quarterly_filing"},
    },
    {
        "id": "annual-report-deadline",
        "text": "Annual compliance reports should include financial summaries, control attestations, material incidents, and evidence of remediation activities.",
        "metadata": {"source": "Default regulatory knowledge base", "topic": "annual_report"},
    },
    {
        "id": "incident-reporting",
        "text": "Incident reports should describe the event, affected systems or customers, immediate containment steps, root cause, and planned mitigation.",
        "metadata": {"source": "Default regulatory knowledge base", "topic": "incident_report"},
    },
]


def _tokenise(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _cosine_similarity(left: Counter, right: Counter) -> float:
    common = set(left) & set(right)
    numerator = sum(left[token] * right[token] for token in common)
    left_norm = math.sqrt(sum(value * value for value in left.values()))
    right_norm = math.sqrt(sum(value * value for value in right.values()))
    if not left_norm or not right_norm:
        return 0.0
    return numerator / (left_norm * right_norm)


class ChromaClientService:
    """
    Wraps ChromaDB for embedding + retrieval.
    Model is pre-loaded at startup to avoid cold-start latency on first request.
    """

    def __init__(self):
        if CHROMA_IMPORT_ERROR is not None:
            self._fallback_reason = str(CHROMA_IMPORT_ERROR)
            self._fallback_docs = [doc.copy() for doc in DEFAULT_KB_DOCUMENTS]
            self._fallback_vectors = {
                doc["id"]: Counter(_tokenise(doc["text"])) for doc in self._fallback_docs
            }
            logger.info(
                "ChromaDB dependencies unavailable. Using in-memory retrieval fallback. Cause: %s",
                self._fallback_reason,
            )
            return

        self._fallback_reason = None

        logger.info("Loading sentence-transformer model '%s'...", EMBED_MODEL_NAME)
        self.embed_model = SentenceTransformer(EMBED_MODEL_NAME)
        logger.info("Sentence-transformer model loaded.")

        self.chroma = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.chroma.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        doc_count = self.collection.count()
        logger.info(
            "ChromaDB ready. Collection '%s' contains %d documents.",
            COLLECTION_NAME, doc_count,
        )

    def embed(self, text: str) -> list[float]:
        if self._fallback_reason is not None:
            counts = Counter(_tokenise(text))
            return [float(counts[token]) for token in sorted(counts)]
        return self.embed_model.encode(text).tolist()

    def add_document(self, doc_id: str, text: str, metadata: dict | None = None) -> bool:
        """Add or update a single document in the collection."""
        if self._fallback_reason is not None:
            doc = {"id": doc_id, "text": text, "metadata": metadata or {}}
            self._fallback_docs = [item for item in self._fallback_docs if item["id"] != doc_id]
            self._fallback_docs.append(doc)
            self._fallback_vectors[doc_id] = Counter(_tokenise(text))
            return True

        try:
            embedding = self.embed(text)
            self.collection.upsert(
                ids=[doc_id],
                embeddings=[embedding],
                documents=[text],
                metadatas=[metadata or {}],
            )
            return True
        except Exception as e:
            logger.error("ChromaDB add_document error: %s", str(e))
            return False

    def add_documents_batch(self, documents: list[dict]) -> int:
        """
        Batch upsert. Each doc dict must have: id, text, metadata (optional).
        Returns count of successfully added docs.
        """
        ids, embeddings, texts, metadatas = [], [], [], []
        if self._fallback_reason is not None:
            added = 0
            for doc in documents:
                if self.add_document(doc["id"], doc["text"], doc.get("metadata", {})):
                    added += 1
            return added

        for doc in documents:
            try:
                emb = self.embed(doc["text"])
                ids.append(doc["id"])
                embeddings.append(emb)
                texts.append(doc["text"])
                metadatas.append(doc.get("metadata", {}))
            except Exception as e:
                logger.warning("Skipping doc %s due to embed error: %s", doc.get("id"), str(e))

        if not ids:
            return 0
        try:
            self.collection.upsert(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
            logger.info("Batch upserted %d documents into ChromaDB.", len(ids))
            return len(ids)
        except Exception as e:
            logger.error("ChromaDB batch upsert error: %s", str(e))
            return 0

    def query(self, question: str, top_k: int = 3) -> list[dict]:
        """
        Embed the question and retrieve top_k most similar chunks.
        Returns list of {text, metadata, distance} dicts.
        """
        if self._fallback_reason is not None:
            query_vector = Counter(_tokenise(question))
            ranked = []
            for doc in self._fallback_docs:
                similarity = _cosine_similarity(
                    query_vector,
                    self._fallback_vectors.get(doc["id"], Counter()),
                )
                ranked.append((similarity, doc))

            ranked.sort(key=lambda item: item[0], reverse=True)
            return [
                {
                    "text": doc["text"],
                    "metadata": doc.get("metadata", {}),
                    "distance": round(1.0 - similarity, 4),
                }
                for similarity, doc in ranked[: max(1, top_k)]
                if similarity > 0
            ]

        try:
            embedding = self.embed(question)
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=min(top_k, max(1, self.collection.count())),
                include=["documents", "metadatas", "distances"],
            )
            chunks = []
            for i, doc in enumerate(results["documents"][0]):
                chunks.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i],
                    "distance": round(results["distances"][0][i], 4),
                })
            return chunks
        except Exception as e:
            logger.error("ChromaDB query error: %s", str(e))
            return []

    def get_doc_count(self) -> int:
        if self._fallback_reason is not None:
            return len(self._fallback_docs)
        try:
            return self.collection.count()
        except Exception:
            return -1

    def get_status(self) -> str:
        if self._fallback_reason is not None:
            return "fallback_in_memory"
        return "healthy"


# Singleton — pre-loads model at import time (startup)
_chroma_service: ChromaClientService | None = None


def get_chroma_service() -> ChromaClientService:
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaClientService()
    return _chroma_service

"""Dense rubric index built with LlamaIndex and stored in Chroma.

Why this exists next to `rag.py`: the lexical scorer in `rag.py` needs nothing
but SQLite and can never fail, which makes it the right fallback on a machine
with no models installed. It is, however, coarse. It matches words, so it misses
a scheme clause that says "present perfect" when the syllabus says "completed
actions with relevance to now", and it ranks a whole page above the one
paragraph that matters.

This module keeps the same SQLite chunks as the source of truth, embeds them
with an Ollama embedding model (`nomic-embed-text` by default) and answers
queries with LlamaIndex's vector retriever over a per-teacher Chroma collection.
Nothing leaves the machine. If Chroma, LlamaIndex or the embedding model is
missing, `search()` returns an empty string and `rag.search()` quietly uses the
lexical path, so a half-installed environment still marks papers.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from app.core.config import settings
from app.db import SessionLocal
from app.models import Chunk, KnowledgeSource
from app.rag.embeddings import chroma_client, embed_model

log = logging.getLogger(__name__)

# Collections already known to match the database in this process.
_ready: set[str] = set()
_dirty: set[str] = set()


def _collection_name(user_id: str) -> str:
    digest = hashlib.sha1((user_id or "anon").encode("utf-8")).hexdigest()[:16]
    return f"{settings.chroma_collection}_{digest}"


def mark_dirty(user_id: str) -> None:
    """Called after a source is (re)indexed so the next search rebuilds."""
    _dirty.add(user_id)
    _ready.discard(user_id)



def _nodes(user_id: str):
    """One TextNode per stored chunk, with the metadata retrieval filters on."""
    from llama_index.core.schema import TextNode

    with SessionLocal() as db:
        rows = (
            db.query(
                Chunk.id,
                Chunk.text,
                Chunk.ordinal,
                KnowledgeSource.kind,
                KnowledgeSource.title,
                KnowledgeSource.year,
            )
            .join(KnowledgeSource, Chunk.source_id == KnowledgeSource.id)
            .filter(KnowledgeSource.user_id == user_id)
            .all()
        )

    nodes = []
    for chunk_id, text, ordinal, kind, title, year in rows:
        if not text:
            continue
        nodes.append(
            TextNode(
                id_=f"chunk-{chunk_id}",
                text=text,
                metadata={
                    "user_id": user_id,
                    "kind": kind or "Knowledge",
                    "title": title or "",
                    "year": year or "",
                    "ordinal": ordinal or 0,
                },
            )
        )
    return nodes


def _chunk_count(user_id: str) -> int:
    with SessionLocal() as db:
        return (
            db.query(Chunk.id)
            .join(KnowledgeSource, Chunk.source_id == KnowledgeSource.id)
            .filter(KnowledgeSource.user_id == user_id)
            .count()
        )


def build(user_id: str):
    """(Re)build this teacher's collection from the SQLite chunks."""
    from llama_index.core import StorageContext, VectorStoreIndex, Settings as LISettings
    from llama_index.vector_stores.chroma import ChromaVectorStore

    LISettings.embed_model = embed_model()

    client = chroma_client()
    name = _collection_name(user_id)
    try:
        client.delete_collection(name)
    except Exception:  # noqa: BLE001 - a missing collection is the normal first run
        pass
    collection = client.get_or_create_collection(name)

    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage = StorageContext.from_defaults(vector_store=vector_store)

    nodes = _nodes(user_id)
    if not nodes:
        _ready.add(user_id)
        _dirty.discard(user_id)
        return 0

    VectorStoreIndex(nodes, storage_context=storage, show_progress=False)
    _ready.add(user_id)
    _dirty.discard(user_id)
    return len(nodes)


def ensure(user_id: str) -> bool:
    """True when a collection matching the current database is ready."""
    if user_id in _ready and user_id not in _dirty:
        return True
    try:
        expected = _chunk_count(user_id)
        client = chroma_client()
        name = _collection_name(user_id)
        try:
            collection = client.get_collection(name)
            stored = collection.count()
        except Exception:  # noqa: BLE001 - no collection yet
            stored = -1
        if stored != expected or user_id in _dirty:
            build(user_id)
        else:
            _ready.add(user_id)
        return True
    except Exception as exc:  # noqa: BLE001 - fall back to lexical retrieval
        log.warning("dense index unavailable for %s: %s", user_id, exc)
        return False


def search(user_id: str, query: str, limit: int | None = None) -> str:
    """Nearest rubric chunks for this query, formatted for the marking prompt.

    Returns "" when the dense path cannot run, which tells `rag.search()` to use
    the lexical scorer instead.
    """
    if (settings.retrieval_mode or "dense").lower() != "dense":
        return ""
    if not (query or "").strip():
        return ""
    if not ensure(user_id):
        return ""

    from llama_index.core import VectorStoreIndex, Settings as LISettings
    from llama_index.vector_stores.chroma import ChromaVectorStore

    try:
        LISettings.embed_model = embed_model()
        collection = chroma_client().get_collection(_collection_name(user_id))
        index = VectorStoreIndex.from_vector_store(
            ChromaVectorStore(chroma_collection=collection),
            embed_model=LISettings.embed_model,
        )
        hits = index.as_retriever(similarity_top_k=limit or settings.retrieval_k).retrieve(
            (query or "")[:4000]
        )
    except Exception as exc:  # noqa: BLE001 - fall back to lexical retrieval
        log.warning("dense retrieval failed for %s: %s", user_id, exc)
        return ""

    parts: list[str] = []
    used = 0
    for hit in hits:
        meta = hit.metadata or {}
        block = f"[{meta.get('kind') or 'Knowledge'} · {meta.get('title') or ''}]\n{hit.text}".strip()
        if used + len(block) > settings.retrieval_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts)


def status(user_id: str) -> dict:
    """What the knowledge screen and the evaluation harness report."""
    try:
        collection = chroma_client().get_collection(_collection_name(user_id))
        vectors = collection.count()
    except Exception:  # noqa: BLE001
        vectors = 0
    return {
        "mode": (settings.retrieval_mode or "dense").lower(),
        "embed_model": settings.ollama_embed_model,
        "collection": _collection_name(user_id),
        "vectors": vectors,
        "chunks": _chunk_count(user_id),
        "ready": vectors == _chunk_count(user_id),
    }


def reset(user_id: str) -> None:
    try:
        chroma_client().delete_collection(_collection_name(user_id))
    except Exception:  # noqa: BLE001
        pass
    _ready.discard(user_id)
    _dirty.add(user_id)
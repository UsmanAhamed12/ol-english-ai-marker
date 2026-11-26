"""The embedding model and the Chroma client.

Both are created lazily: importing this module must not start a model or open a
database, because most requests never touch the vector index. ``nomic-embed-text``
runs inside Ollama, so embedding a syllabus page costs nothing and sends nothing
off the machine.
"""

from pathlib import Path

from app.core.config import settings


def chroma_client():
    """The one persistent Chroma database on disk (``data/chroma``)."""
    import chromadb

    return chromadb.PersistentClient(path=str(Path(settings.chroma_dir).resolve()))


def embed_model():
    """Ollama's embedding model, asked to stay loaded for the whole marking run."""
    from llama_index.embeddings.ollama import OllamaEmbedding

    return OllamaEmbedding(
        model_name=settings.ollama_embed_model,
        base_url=settings.ollama_base_url,
        ollama_additional_kwargs={"keep_alive": "30m"},
    )
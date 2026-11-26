from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration comes from the environment. No secret is ever hard-coded."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Red Pen"
    environment: str = "development"

    # Auth
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720

    # Local AI through Ollama — no cloud, no API key, no per-paper cost.
    # `ollama serve` must be running. Three small models share the work (about
    # 5 GB on disk, comfortable on a 16 GB laptop):
    #   * glm-ocr reads the scanned pages (printed and handwritten layers);
    #   * llama3.2:3b marks each test and writes the feedback;
    #   * nomic-embed-text embeds the rubric chunks for retrieval.
    # llama3.1:8b is a drop-in upgrade for marking (see docs/ollama_setup.md).
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_timeout: int = 900
    ollama_num_ctx: int = 12288
    ollama_num_predict: int = 2600
    ollama_model: str = "llama3.2:3b"
    ollama_ocr_model: str = "glm-ocr:latest"
    # GLM-OCR is task-prompted, not chat-prompted: this is the one instruction it knows.
    ocr_prompt: str = "Text Recognition:"

    # Storage
    database_url: str = "sqlite:///./data/gradewise.db"
    private_dir: str = "./data/uploads"

    # Upload limits
    max_upload_mb: int = 200
    max_files: int = 6
    max_pages: int = 40

    # Page reading: pages are rendered in colour at 200 DPI so the ink colour can
    # tell the student's pen from the printed paper (see app/rag/ink.py).
    ocr_min_chars: int = 60
    ocr_dpi: int = 200
    ocr_quality: int = 82
    # Fewer coloured-ink pixels than this means "no handwriting layer found".
    ink_min_pixels: int = 250
    # How much of a page's printed text goes to the marker (the answers are what
    # it needs; the printed question only gives context).
    printed_chars_per_page: int = 700

    # Prompt budget (characters), keeps requests inside the model context window.
    # A 12k-token window: 20k characters of prompt still leaves room for a full
    # 16-test JSON report.
    prompt_chars: int = 20000

    # Knowledge base. "dense" uses the LlamaIndex collection (Chroma vectors
    # embedded by Ollama); "lexical" forces the keyword scorer that needs no
    # model. Dense retrieval falls back to lexical automatically when the
    # embedding model or the vector store is unavailable.
    retrieval_mode: str = "dense"
    retrieval_k: int = 8
    retrieval_chars: int = 6000
    ollama_embed_model: str = "nomic-embed-text"
    chroma_dir: str = "./data/chroma"
    chroma_collection: str = "ol_english_rubric"

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def is_prod(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def upload_dir(self) -> Path:
        path = Path(self.private_dir).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def vector_dir(self) -> Path:
        path = Path(self.chroma_dir).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
"""Which local Ollama models exist, and which one marks papers.

Open this first when marking fails: it shows whether Ollama is running, whether the
configured model is installed, and the exact names you can put in backend/.env.
"""

from fastapi import APIRouter

from app.rag.llm import models_status

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/api/health/ai")
def ai_health() -> dict:
    status = models_status()
    return {
        "provider": "ollama",
        "base_url": status["base_url"],
        "text_model": status["text_model"],
        "text_present": status["text_present"],
        "ocr_model": status["ocr_model"],
        "ocr_present": status["ocr_present"],
        "models_available": len(status["available"]),
        "installed_models": status["available"],
        "error": status["error"],
    }
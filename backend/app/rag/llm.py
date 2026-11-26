"""Local AI through Ollama — no cloud, no API key, no per-paper cost.

Everything runs against the Ollama daemon on this machine (default
http://127.0.0.1:11434). Three small models share the work, all configurable:

* **Reading.** `glm-ocr` (`OLLAMA_OCR_MODEL`) turns a page image into text. It is
  a dedicated OCR model (about 2.7 GB), so it is fast on a laptop and takes one
  fixed instruction, "Text Recognition:". Printed and handwritten ink are split
  into two images first (app/rag/ink.py) and read separately.
* **Marking.** `llama3.2:3b` (`OLLAMA_MODEL`) marks each test against the scheme
  and writes feedback, tips and knowledge gaps. `llama3.1:8b` is a stronger
  drop-in on a 16 GB machine.
* **Retrieval.** `nomic-embed-text` embeds the rubric chunks.
* Prompts are clipped to `PROMPT_CHARS` and replies to `OLLAMA_NUM_PREDICT` tokens.
"""

import json
import re

import httpx

from app.core.config import settings

DEFAULT_BASE = "http://127.0.0.1:11434"


class AIError(RuntimeError):
    """An error whose message is safe and useful to show to the teacher."""


# ------------------------------------------------------------------ plumbing


def _base() -> str:
    return (settings.ollama_base_url or DEFAULT_BASE).rstrip("/")


def _offline() -> AIError:
    return AIError(
        f"Ollama is not answering at {_base()}. Start it with `ollama serve`, check that the "
        "Ollama app is running, then try again."
    )


def _clip(prompt: str) -> str:
    limit = max(2000, settings.prompt_chars)
    text = str(prompt or "")
    return text if len(text) <= limit else text[:limit]


def list_models() -> list[str]:
    """Tags installed for this machine. Empty list when Ollama is not running."""
    try:
        response = httpx.get(f"{_base()}/api/tags", timeout=8)
    except httpx.HTTPError:
        return []
    if response.status_code != 200:
        return []
    try:
        return [
            str(row.get("name") or "")
            for row in response.json().get("models", [])
            if row.get("name")
        ]
    except ValueError:
        return []


def _installed(model: str, models: list[str]) -> bool:
    name = (model or "").strip()
    if not name:
        return False
    if name in models:
        return True
    plain = name.split(":")[0]
    return any(m.split(":")[0] == plain and (":" not in name or m.endswith(":latest")) for m in models)


def _check_model(model: str, models: list[str]) -> None:
    if models and not _installed(model, models):
        raise AIError(
            f"The model `{model}` is not installed. Run `ollama pull {model}`, then try again."
        )


def _chat(model: str, messages: list, *, json_mode: bool, max_tokens: int) -> str:
    payload: dict = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0,
            "num_ctx": max(1024, settings.ollama_num_ctx),
            "num_predict": min(max_tokens, max(64, settings.ollama_num_predict)),
        },
    }
    if json_mode:
        payload["format"] = "json"

    try:
        response = httpx.post(
            f"{_base()}/api/chat",
            json=payload,
            timeout=settings.ollama_timeout,
        )
    except httpx.ConnectError as exc:
        raise _offline() from exc
    except httpx.TimeoutException as exc:
        raise AIError(
            f"`{model}` took longer than {settings.ollama_timeout}s to answer. A local model is slow "
            "on CPU — try a shorter paper, or raise OLLAMA_TIMEOUT in backend/.env."
        ) from exc
    except httpx.HTTPError as exc:
        raise AIError(
            f"Could not reach Ollama ({type(exc).__name__}). Is `ollama serve` running?"
        ) from exc

    if response.status_code == 404:
        raise AIError(
            f"The model `{model}` is not installed. Run `ollama pull {model}`, then try again."
        )
    if response.status_code != 200:
        detail = ""
        try:
            detail = str(response.json().get("error") or "")
        except ValueError:
            detail = (response.text or "")[:200]
        lowered = detail.lower()
        if "no such model" in lowered or "not found" in lowered:
            raise AIError(f"The model `{model}` is not installed. Run `ollama pull {model}`.")
        raise AIError(f"Ollama refused the request: {detail or response.status_code}")

    try:
        body = response.json()
    except ValueError as exc:
        raise AIError("Ollama returned an unreadable reply. Try again.") from exc

    return str((body.get("message") or {}).get("content") or "").strip()


def _loads(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?|```$", "", (text or "").strip(), flags=re.M).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(cleaned[start : end + 1])
            except json.JSONDecodeError:
                pass
    raise AIError(
        "The local model did not return readable JSON - it lost the format on a long answer. Run the "
        "paper again; if it repeats, give the model more room (OLLAMA_NUM_PREDICT=3500 in backend/.env) "
        "or use a stronger marking model (`ollama pull llama3.1:8b`, then OLLAMA_MODEL=llama3.1:8b). "
        "Reading the scan is done by glm-ocr and is not affected."
    )


# ------------------------------------------------------------------ public


def complete_text(prompt: str, *, max_tokens: int = 1200) -> str:
    models = list_models()
    _check_model(settings.ollama_model, models)
    return _chat(
        settings.ollama_model,
        [{"role": "user", "content": _clip(prompt)}],
        json_mode=False,
        max_tokens=max_tokens,
    )


def complete_json(prompt: str, *, max_tokens: int = 1600) -> dict:
    models = list_models()
    _check_model(settings.ollama_model, models)

    messages = [
        {
            "role": "system",
            "content": "You reply with one valid JSON object only. No commentary, no markdown fences.",
        },
        {"role": "user", "content": _clip(prompt)},
    ]

    text = _chat(settings.ollama_model, messages, json_mode=True, max_tokens=max_tokens)
    try:
        return _loads(text)
    except AIError:
        # One plain retry: some small models answer worse when forced into JSON mode.
        text = _chat(settings.ollama_model, messages, json_mode=False, max_tokens=max_tokens)
        return _loads(text)


def ocr_image(image_b64: str, mime: str = "image/png", prompt: str = "", *, max_tokens: int = 2600) -> str:
    """Read one page image with the local GLM-OCR model.

    GLM-OCR is task-prompted: it answers the fixed instruction "Text Recognition:"
    and ignores free-form prompts, so `prompt` is accepted only for call-site
    compatibility and the configured instruction is always used.
    """
    model = (settings.ollama_ocr_model or "").strip()
    if not model:
        raise AIError(
            "No OCR model is configured. Run `ollama pull glm-ocr`, set OLLAMA_OCR_MODEL=glm-ocr:latest "
            "in backend/.env, restart the API, then try again."
        )

    models = list_models()
    _check_model(model, models)

    messages = [{"role": "user", "content": settings.ocr_prompt, "images": [image_b64]}]
    return _chat(model, messages, json_mode=False, max_tokens=max_tokens)


def models_status() -> dict:
    """What /api/health/ai reports: which local models exist and what will be used."""
    models = list_models()
    text = settings.ollama_model
    ocr = (settings.ollama_ocr_model or "").strip()

    error = ""
    if not models:
        error = (
            f"Ollama is not running at {_base()}. Open the Ollama app or run `ollama serve`, then "
            "refresh this page."
        )
    elif not _installed(text, models):
        error = f"The model `{text}` is not installed. Run `ollama pull {text}`."
    elif ocr and not _installed(ocr, models):
        error = f"The OCR model `{ocr}` is not installed. Run `ollama pull glm-ocr`."

    return {
        "base_url": _base(),
        "text_model": text,
        "text_present": _installed(text, models),
        "ocr_model": ocr,
        "ocr_present": _installed(ocr, models) if ocr else False,
        "available": models,
        "error": error,
    }
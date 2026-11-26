"""The single router mounted by ``main.py``.

Each resource module owns its own prefix and tags, so this file stays a list:

    /api/health      health.py   - is the service up, are the Ollama models installed
    /api/auth        auth.py     - register, sign in, who am I
    /api/papers      papers.py   - upload a script, list papers, open one
    /api/papers      marking.py  - start a marking run, delete a paper, download a file
    /api/knowledge   rubrics.py  - the teacher's knowledge base
"""

from fastapi import APIRouter

from app.api.v1.routes import auth, health, marking, papers, rubrics

api_router = APIRouter()

for module in (health, auth, papers, marking, rubrics):
    api_router.include_router(module.router)
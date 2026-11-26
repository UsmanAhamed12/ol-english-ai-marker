"""Test setup: a throwaway environment so nothing touches the real database.

The application reads all configuration from the environment, so the tests set a
secret and a temporary SQLite file before any application module is imported.
"""

import os
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

_TMP = tempfile.mkdtemp(prefix="redpen-tests-")
os.environ.setdefault("JWT_SECRET", "test-secret-not-used-anywhere-else")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{_TMP}/test.db")
os.environ.setdefault("PRIVATE_DIR", f"{_TMP}/uploads")
os.environ.setdefault("CHROMA_DIR", f"{_TMP}/chroma")
os.environ.setdefault("RETRIEVAL_MODE", "lexical")
os.environ.setdefault("ENVIRONMENT", "test")
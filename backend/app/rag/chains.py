"""The two chains a marking run uses.

A "chain" here is deliberately small: build the prompt, ask the local model, get
JSON back. Keeping them in one module means the marking graph reads as steps
(validate -> read -> inventory -> retrieve -> mark) instead of prompt plumbing.
"""

from app.rag.llm import complete_json
from app.rag.prompts import build_inventory_prompt, build_marking_prompt


def inventory_chain(scheme_text: str, script_text: str) -> dict:
    """Step 1: the paper's own question list, read before any marks are given.

    Marking against a checklist is what stops a 16-test paper coming back with
    nine lines because the model lost interest halfway.
    """
    return complete_json(
        build_inventory_prompt(scheme_text, script_text),
        max_tokens=3000,
    )


def marking_chain(job, script_text: str, scheme_text: str, context: str, inventory: list[dict]) -> dict:
    """Step 2: mark every question and write the report, as JSON."""
    return complete_json(
        build_marking_prompt(job, script_text, scheme_text, context, inventory),
        max_tokens=8000,
    )
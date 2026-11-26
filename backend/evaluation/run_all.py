"""Run every evaluation and write one summary.

    cd backend
    python -m evaluation.run_all

Nothing here calls a model: the fixtures are fixed, so the numbers are
reproducible on any machine and can be checked by a second marker.
"""

from __future__ import annotations

import json
import pathlib

from evaluation import evaluate_marking, evaluate_ocr, evaluate_retrieval, evaluate_structure

RESULTS = pathlib.Path(__file__).resolve().parent / "results"


def main() -> dict:
    RESULTS.mkdir(exist_ok=True)
    summary = {
        "structure": evaluate_structure.main(),
        "reading": evaluate_ocr.main()["readers"],
        "retrieval": evaluate_retrieval.main()["retrievers"],
        "marking": evaluate_marking.main(),
    }
    (RESULTS / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nWritten to {RESULTS}/summary.json")
    return summary


if __name__ == "__main__":
    main()
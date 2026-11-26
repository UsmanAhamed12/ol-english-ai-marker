"""Structure detection: does the system find every test the paper contains?

The pipeline reads the paper's inventory from the scheme before marking, so a
missed test is a test that silently scores zero. This measures that step on its
own, which is why it is reported separately from marking agreement.

    cd backend
    python -m evaluation.evaluate_structure
"""

from __future__ import annotations

import json
import pathlib

from evaluation.metrics import prf1

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "datasets" / "structure_ground_truth.json"
RESULTS = HERE / "results"


def evaluate(data: dict | None = None) -> dict:
    data = data or json.loads(DATA.read_text(encoding="utf-8"))

    true_positive = false_positive = false_negative = expected_total = 0
    per_paper = []

    for paper in data["papers"]:
        expected = {str(value) for value in paper["expected"]}
        detected = {str(value) for value in paper["detected"]}
        tp = len(expected & detected)
        fp = len(detected - expected)
        fn = len(expected - detected)
        true_positive += tp
        false_positive += fp
        false_negative += fn
        expected_total += len(expected)
        per_paper.append(
            {
                "paper_id": paper["paper_id"],
                "expected": len(expected),
                "detected": len(detected),
                "missed": sorted(expected - detected),
                "spurious": sorted(detected - expected),
            }
        )

    scores = prf1(true_positive, false_positive, false_negative)
    return {
        "papers": len(data["papers"]),
        "expected_tests": expected_total,
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": round(scores["precision"], 3),
        "recall": round(scores["recall"], 3),
        "f1": round(scores["f1"], 3),
        "per_paper": per_paper,
    }


def main() -> dict:
    result = evaluate()
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "structure_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [
        "| Metric | Value |",
        "| --- | --- |",
        f"| Scripts | {result['papers']} |",
        f"| Tests on the papers | {result['expected_tests']} |",
        f"| Precision | {result['precision']} |",
        f"| Recall | {result['recall']} |",
        f"| F1 | {result['f1']} |",
        f"| Tests missed | {result['false_negative']} |",
    ]
    (RESULTS / "structure_metrics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\nStructure detection\n")
    print("\n".join(lines))
    return result


if __name__ == "__main__":
    main()
"""Marking agreement: how close the system's total is to the teacher's total.

The fixture holds twenty scripts that one teacher marked by hand before the
system saw them, paired with the normalised total the system produced. Replacing
`datasets/marking_ground_truth.jsonl` with your own marked scripts reproduces
the same tables for your cohort.

    cd backend
    python -m evaluation.evaluate_marking
"""

from __future__ import annotations

import json
import pathlib

from evaluation.metrics import (
    accuracy,
    band,
    bias,
    classification_report,
    mae,
    pearson,
    quadratic_weighted_kappa,
    rmse,
    spearman,
)

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "datasets" / "marking_ground_truth.jsonl"
RESULTS = HERE / "results"
BANDS = ["A", "B", "C", "S", "F"]


def load() -> list[dict]:
    rows = []
    with DATA.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def evaluate(rows: list[dict] | None = None) -> dict:
    rows = rows if rows is not None else load()
    human = [float(row["human_total"]) for row in rows]
    system = [float(row["system_total"]) for row in rows]

    human_bands = [band(value) for value in human]
    system_bands = [band(value) for value in system]
    report = classification_report(human_bands, system_bands, BANDS)

    within_five = sum(1 for h, s in zip(human, system) if abs(h - s) <= 5) / len(rows)
    within_ten = sum(1 for h, s in zip(human, system) if abs(h - s) <= 10) / len(rows)

    errors = [abs(h - s) for h, s in zip(human, system)]
    largest = max(range(len(rows)), key=lambda i: errors[i])

    return {
        "papers": len(rows),
        "mae": round(mae(human, system), 2),
        "rmse": round(rmse(human, system), 2),
        "bias": round(bias(human, system), 2),
        "qwk": round(quadratic_weighted_kappa(human, system), 3),
        "pearson": round(pearson(human, system), 3),
        "spearman": round(spearman(human, system), 3),
        "band_accuracy": round(accuracy(human_bands, system_bands), 3),
        "macro_f1": round(report["macro"]["f1"], 3),
        "micro_f1": round(report["micro"]["f1"], 3),
        "per_band": {
            label: {key: round(value, 3) for key, value in report["per_label"][label].items()}
            for label in BANDS
        },
        "within_5_marks": round(within_five, 3),
        "within_10_marks": round(within_ten, 3),
        "largest_difference": {
            "paper_id": rows[largest]["paper_id"],
            "human": human[largest],
            "system": system[largest],
            "difference": round(errors[largest], 1),
        },
    }


def main() -> dict:
    result = evaluate()
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "marking_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [
        "| Metric | Value |",
        "| --- | --- |",
        f"| Scripts compared | {result['papers']} |",
        f"| Mean absolute error | {result['mae']} marks |",
        f"| Root mean squared error | {result['rmse']} marks |",
        f"| Mean signed error (bias) | {result['bias']} marks |",
        f"| Quadratic weighted kappa | {result['qwk']} |",
        f"| Pearson correlation | {result['pearson']} |",
        f"| Spearman rank correlation | {result['spearman']} |",
        f"| Grade band accuracy | {result['band_accuracy'] * 100:.1f}% |",
        f"| Macro F1 over five bands | {result['macro_f1']} |",
        f"| Within 5 marks | {result['within_5_marks'] * 100:.0f}% of scripts |",
        f"| Within 10 marks | {result['within_10_marks'] * 100:.0f}% of scripts |",
    ]
    (RESULTS / "marking_metrics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\nMarking agreement against the teacher\n")
    print("\n".join(lines))
    return result


if __name__ == "__main__":
    main()
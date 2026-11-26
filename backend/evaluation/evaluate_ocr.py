"""Reading quality: how close each reader's transcription is to a human's.

Ground truth is a hand-corrected transcription of the same six handwritten script
pages, so the numbers measure the reader and nothing else. Every reader is
compared on the same pages, which is what makes the comparison fair.

Two views are reported. Character error rate (CER) is the usual measure of an OCR
pipeline. Item accuracy is the one that matters here: a script is marked item by
item, so a single wrong letter in "Completing" turns a correct item into a wrong
one and costs a mark. A reader can look respectable on CER and still be useless
for marking, and the second column shows that.

    cd backend
    python -m evaluation.evaluate_ocr
"""

from __future__ import annotations

import json
import pathlib
import re

from evaluation.metrics import cer, normalise, wer

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "datasets" / "ocr_ground_truth.jsonl"
RESULTS = HERE / "results"

# A page is only usable for marking if its transcript is close enough to be read.
USABLE_CER = 0.15
USABLE_ITEM = 0.75

ITEM = re.compile(r"(\d+)\)\s*(.+?)(?=\s+\d+\)|$)", re.S)


def load() -> list[dict]:
    rows = []
    with DATA.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def parse_items(text: str) -> dict[str, str]:
    """Split a transcript into numbered items, the unit that earns a mark."""
    found = {}
    for number, answer in ITEM.findall(text or ""):
        found[number] = normalise(answer).strip(" .,;")
    return found


def item_accuracy(reference: str, hypothesis: str) -> float | None:
    """Share of numbered items read exactly right. None when the page has no items."""
    expected = parse_items(reference)
    if not expected:
        return None
    got = parse_items(hypothesis)
    correct = sum(1 for number, answer in expected.items() if got.get(number) == answer)
    return correct / len(expected)


def evaluate(rows: list[dict] | None = None) -> dict:
    rows = rows if rows is not None else load()
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row["reader"], []).append(row)

    table = []
    for reader, page_rows in grouped.items():
        character = [cer(row["reference"], row["prediction"]) for row in page_rows]
        word = [wer(row["reference"], row["prediction"]) for row in page_rows]
        item_scores = [
            score
            for score in (item_accuracy(row["reference"], row["prediction"]) for row in page_rows)
            if score is not None
        ]
        worst = max(range(len(page_rows)), key=lambda i: character[i])
        table.append(
            {
                "reader": reader,
                "pages": len(page_rows),
                "cer": round(sum(character) / len(character), 4),
                "wer": round(sum(word) / len(word), 4),
                "item_accuracy": round(sum(item_scores) / len(item_scores), 3) if item_scores else None,
                "cer_best": round(min(character), 4),
                "cer_worst": round(max(character), 4),
                "worst_page": page_rows[worst]["page"],
                "usable_pages": sum(1 for value in character if value <= USABLE_CER),
                "usable_rate": round(
                    sum(1 for value in character if value <= USABLE_CER) / len(page_rows), 3
                ),
            }
        )

    table.sort(key=lambda row: row["cer"])
    return {
        "metric": "character and word error rate, plus item accuracy",
        "threshold": USABLE_CER,
        "usable_item_accuracy": USABLE_ITEM,
        "readers": table,
    }


def main() -> dict:
    result = evaluate()
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "ocr_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [
        "| Reader | Pages | CER | WER | Item accuracy | Usable pages | Worst page |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in result["readers"]:
        item = "n/a" if row["item_accuracy"] is None else f"{row['item_accuracy'] * 100:.0f}%"
        lines.append(
            f"| {row['reader']} | {row['pages']} | {row['cer']:.3f} | {row['wer']:.3f} | {item} "
            f"| {row['usable_pages']}/{row['pages']} | {row['worst_page']} |"
        )
    (RESULTS / "ocr_metrics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\nReading quality (lower CER is better, higher item accuracy is better)\n")
    print("\n".join(lines))
    return result


if __name__ == "__main__":
    main()
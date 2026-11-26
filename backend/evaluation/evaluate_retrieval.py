"""Retrieval quality: does the marker receive the clause it needs?

The log records, for twelve rubric queries, what each retriever returned from the
same corpus. Precision@k, recall@k and MRR are then computed here, so the
comparison between the lexical scorer and the LlamaIndex collection is made on
identical queries rather than on impressions.

    cd backend
    python -m evaluation.evaluate_retrieval
"""

from __future__ import annotations

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
DATA = HERE / "datasets" / "retrieval_runs.json"
RESULTS = HERE / "results"


def load() -> dict:
    return json.loads(DATA.read_text(encoding="utf-8"))


def score_case(retrieved: list[str], relevant: list[str], k: int) -> dict:
    top = retrieved[:k]
    hits = [title for title in top if title in set(relevant)]
    first_rank = next((i + 1 for i, title in enumerate(top) if title in set(relevant)), None)
    return {
        "precision": len(hits) / k if k else 0.0,
        "recall": len(set(hits)) / len(set(relevant)) if relevant else 0.0,
        "mrr": 1 / first_rank if first_rank else 0.0,
        "hit_at_1": 1.0 if top and top[0] in set(relevant) else 0.0,
        "hit_at_3": 1.0 if any(title in set(relevant) for title in top[:3]) else 0.0,
        "hit_at_k": 1.0 if hits else 0.0,
    }


def evaluate(data: dict | None = None) -> dict:
    data = data or load()
    k = int(data.get("k") or 8)
    rows = {"lexical": [], "dense": []}

    for case in data["cases"]:
        for retriever in rows:
            rows[retriever].append(score_case(case.get(retriever, []), case["relevant"], k))

    summary = {}
    for retriever, items in rows.items():
        summary[retriever] = {
            "queries": len(items),
            "k": k,
            "precision_at_k": round(sum(i["precision"] for i in items) / len(items), 3),
            "recall_at_k": round(sum(i["recall"] for i in items) / len(items), 3),
            "mrr": round(sum(i["mrr"] for i in items) / len(items), 3),
            "hit_at_1": round(sum(i["hit_at_1"] for i in items) / len(items), 3),
            "hit_at_3": round(sum(i["hit_at_3"] for i in items) / len(items), 3),
            "hit_at_k": round(sum(i["hit_at_k"] for i in items) / len(items), 3),
        }
    return {"k": k, "retrievers": summary}


def main() -> dict:
    result = evaluate()
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "retrieval_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    lines = [
        "| Retriever | P@k | R@k | MRR | Hit@1 | Hit@3 | Hit@k |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, row in result["retrievers"].items():
        lines.append(
            f"| {name} | {row['precision_at_k']:.3f} | {row['recall_at_k']:.3f} | {row['mrr']:.3f} "
            f"| {row['hit_at_1']:.2f} | {row['hit_at_3']:.2f} | {row['hit_at_k']:.2f} |"
        )
    (RESULTS / "retrieval_metrics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"\nRetrieval quality at k={result['k']}\n")
    print("\n".join(lines))
    return result


if __name__ == "__main__":
    main()
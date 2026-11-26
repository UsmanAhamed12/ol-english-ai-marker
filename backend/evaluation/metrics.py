"""Metrics used by the evaluation harness and by the report's tables.

Pure Python, no model and no network, so the numbers in the report can be
recomputed on any machine with `python -m evaluation.run_all`.

Reported metrics and why each one is here:

* CER / WER        reading quality, character and word level, normalised so 0 is perfect.
* precision/recall/F1  per grade band, because a marker that is always 5 marks high
                    still has a good correlation but is useless in practice.
* MAE / RMSE       how far the system's mark sits from the teacher's, in marks.
* QWK              quadratic weighted kappa, the standard agreement statistic for
                    ordered grades; it punishes a 20-mark miss far more than a 2-mark one.
* Pearson/Spearman rank correlation across papers.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

# ------------------------------------------------------------------ text


def normalise(text: str) -> str:
    """Lowercase, collapse whitespace. Keeps punctuation because it carries marks."""
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _edit_distance(a: list[str] | str, b: list[str] | str) -> int:
    """Levenshtein distance with two rows of memory."""
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, item_a in enumerate(a, start=1):
        current = [i]
        for j, item_b in enumerate(b, start=1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            substitute = previous[j - 1] + (item_a != item_b)
            current.append(min(insert, delete, substitute))
        previous = current
    return previous[-1]


def cer(reference: str, hypothesis: str) -> float:
    """Character error rate: edit distance divided by reference characters."""
    ref = normalise(reference)
    hyp = normalise(hypothesis)
    if not ref:
        return 0.0 if not hyp else 1.0
    return _edit_distance(ref, hyp) / len(ref)


def wer(reference: str, hypothesis: str) -> float:
    """Word error rate on whitespace tokens."""
    ref = normalise(reference).split()
    hyp = normalise(hypothesis).split()
    if not ref:
        return 0.0 if not hyp else 1.0
    return _edit_distance(ref, hyp) / len(ref)


# ------------------------------------------------------------------ classification


def prf1(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"precision": precision, "recall": recall, "f1": f1, "support": tp + fn}


def classification_report(y_true: list, y_pred: list, labels: list[str] | None = None) -> dict:
    """Per-label precision, recall and F1 plus micro and macro averages."""
    labels = labels or sorted({str(v) for v in list(y_true) + list(y_pred)})
    per_label = {}
    for label in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if str(t) == label and str(p) == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if str(t) != label and str(p) == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if str(t) == label and str(p) != label)
        per_label[label] = prf1(tp, fp, fn)

    micro = prf1(
        sum(1 for t, p in zip(y_true, y_pred) if str(t) == str(p)),
        sum(1 for t, p in zip(y_true, y_pred) if str(t) != str(p)),
        sum(1 for t, p in zip(y_true, y_pred) if str(t) != str(p)),
    )
    macro = {
        key: sum(per_label[label][key] for label in labels) / len(labels)
        for key in ("precision", "recall", "f1")
    }
    return {"per_label": per_label, "micro": micro, "macro": macro, "labels": labels}


def accuracy(y_true: list, y_pred: list) -> float:
    if not y_true:
        return 0.0
    return sum(1 for t, p in zip(y_true, y_pred) if t == p) / len(y_true)


# ------------------------------------------------------------------ agreement


def mae(y_true: list[float], y_pred: list[float]) -> float:
    if not y_true:
        return 0.0
    return sum(abs(float(t) - float(p)) for t, p in zip(y_true, y_pred)) / len(y_true)


def rmse(y_true: list[float], y_pred: list[float]) -> float:
    if not y_true:
        return 0.0
    return math.sqrt(sum((float(t) - float(p)) ** 2 for t, p in zip(y_true, y_pred)) / len(y_true))


def bias(y_true: list[float], y_pred: list[float]) -> float:
    """Mean signed error. Positive means the system marks generously."""
    if not y_true:
        return 0.0
    return sum(float(p) - float(t) for t, p in zip(y_true, y_pred)) / len(y_true)


def quadratic_weighted_kappa(
    y_true: list[float], y_pred: list[float], minimum: float = 0.0, maximum: float = 100.0, bins: int = 10
) -> float:
    """QWK over ordered bins, the agreement measure used for exam grades.

    1.0 is perfect agreement, 0.0 is chance. Values above 0.6 are usually read as
    substantial agreement in assessment research (Cohen, 1960).
    """
    if not y_true or len(y_true) != len(y_pred):
        return 0.0

    width = (maximum - minimum) / bins

    def bucket(value: float) -> int:
        index = int((float(value) - minimum) / width)
        return max(0, min(bins - 1, index))

    observed = [[0.0] * bins for _ in range(bins)]
    for t, p in zip(y_true, y_pred):
        observed[bucket(t)][bucket(p)] += 1

    total = float(len(y_true))
    hist_true = [sum(observed[i]) for i in range(bins)]
    hist_pred = [sum(observed[i][j] for i in range(bins)) for j in range(bins)]

    numerator = 0.0
    denominator = 0.0
    for i in range(bins):
        for j in range(bins):
            weight = ((i - j) ** 2) / ((bins - 1) ** 2)
            numerator += weight * observed[i][j]
            denominator += weight * (hist_true[i] * hist_pred[j] / total)
    if denominator == 0:
        return 1.0
    return 1 - numerator / denominator


def pearson(y_true: list[float], y_pred: list[float]) -> float:
    if len(y_true) < 2:
        return 0.0
    mean_t = sum(y_true) / len(y_true)
    mean_p = sum(y_pred) / len(y_pred)
    cov = sum((t - mean_t) * (p - mean_p) for t, p in zip(y_true, y_pred))
    var_t = math.sqrt(sum((t - mean_t) ** 2 for t in y_true))
    var_p = math.sqrt(sum((p - mean_p) ** 2 for p in y_pred))
    return cov / (var_t * var_p) if var_t and var_p else 0.0


def _ranks(values: list[float]) -> list[float]:
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        average = (i + j) / 2 + 1
        for k in range(i, j + 1):
            ranks[order[k]] = average
        i = j + 1
    return ranks


def spearman(y_true: list[float], y_pred: list[float]) -> float:
    if len(y_true) < 2:
        return 0.0
    return pearson(_ranks(list(y_true)), _ranks(list(y_pred)))


def band(score: float) -> str:
    """Grade band used by the Sri Lankan O/L scale, applied to the mark out of 100."""
    if score >= 75:
        return "A"
    if score >= 65:
        return "B"
    if score >= 55:
        return "C"
    if score >= 35:
        return "S"
    return "F"


def group_mean(rows: list[dict], key: str, value: str) -> dict:
    """Mean of value grouped by key, used for per-test error breakdowns."""
    buckets: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        buckets[str(row.get(key))].append(float(row.get(value) or 0))
    return {name: sum(items) / len(items) for name, items in buckets.items() if items}
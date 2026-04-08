from __future__ import annotations

import csv
import itertools
from pathlib import Path


def _load_column(path: str | Path, column: str) -> list[str]:
    with open(path, newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [row[column] for row in reader]


def _pairwise_f1(true_labels: list[str], pred_labels: list[str]) -> float:
    true_pairs = set()
    pred_pairs = set()

    for left, right in itertools.combinations(range(len(true_labels)), 2):
        if true_labels[left] == true_labels[right]:
            true_pairs.add((left, right))
        if pred_labels[left] == pred_labels[right]:
            pred_pairs.add((left, right))

    if not true_pairs and not pred_pairs:
        return 1.0

    true_positive = len(true_pairs & pred_pairs)
    precision = true_positive / len(pred_pairs) if pred_pairs else 0.0
    recall = true_positive / len(true_pairs) if true_pairs else 0.0
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def evaluate(groundtruth: str, parsedresult: str) -> tuple[float, float]:
    gt_templates = _load_column(groundtruth, "EventTemplate")
    parsed_templates = _load_column(parsedresult, "EventTemplate")
    gt_ids = _load_column(groundtruth, "EventId")
    parsed_ids = _load_column(parsedresult, "EventId")

    line_count = min(len(gt_templates), len(parsed_templates), len(gt_ids), len(parsed_ids))
    if line_count == 0:
        return 0.0, 0.0

    gt_templates = gt_templates[:line_count]
    parsed_templates = parsed_templates[:line_count]
    gt_ids = gt_ids[:line_count]
    parsed_ids = parsed_ids[:line_count]

    accuracy = sum(1 for left, right in zip(gt_templates, parsed_templates) if left == right) / line_count
    f1_measure = _pairwise_f1(gt_ids, parsed_ids)
    return f1_measure, accuracy
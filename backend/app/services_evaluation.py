from __future__ import annotations

import re
from collections.abc import Iterable


def _tokens(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower(), flags=re.UNICODE)


def _edit_distance(left: list[str], right: list[str]) -> int:
    previous = list(range(len(right) + 1))
    for row, left_value in enumerate(left, start=1):
        current = [row]
        for column, right_value in enumerate(right, start=1):
            current.append(min(
                current[-1] + 1,
                previous[column] + 1,
                previous[column - 1] + (left_value != right_value),
            ))
        previous = current
    return previous[-1]


def wer(reference: str, hypothesis: str) -> float:
    reference_tokens = _tokens(reference)
    if not reference_tokens:
        return 0.0 if not _tokens(hypothesis) else 1.0
    return _edit_distance(reference_tokens, _tokens(hypothesis)) / len(reference_tokens)


def cer(reference: str, hypothesis: str) -> float:
    reference_chars = list(reference.strip().lower())
    if not reference_chars:
        return 0.0 if not hypothesis.strip() else 1.0
    return _edit_distance(reference_chars, list(hypothesis.strip().lower())) / len(reference_chars)


def _entity_key(value: object) -> str:
    if isinstance(value, str):
        return value.strip().casefold()
    if isinstance(value, dict):
        category = str(value.get("category", "")).casefold()
        text = str(value.get("text", value.get("value", ""))).strip().casefold()
        return f"{category}:{text}"
    return str(value).strip().casefold()


def entity_metrics(reference: Iterable[object], predicted: Iterable[object]) -> dict[str, float | int]:
    expected = {_entity_key(item) for item in reference if _entity_key(item)}
    actual = {_entity_key(item) for item in predicted if _entity_key(item)}
    true_positive = len(expected & actual)
    false_positive = len(actual - expected)
    false_negative = len(expected - actual)
    precision = true_positive / len(actual) if actual else (1.0 if not expected else 0.0)
    recall = true_positive / len(expected) if expected else (1.0 if not actual else 0.0)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "true_positive": true_positive,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "precision": round(precision, 6),
        "recall": round(recall, 6),
        "f1": round(f1, 6),
    }


def score_corpus(examples: list[dict]) -> dict[str, object]:
    if not examples:
        raise ValueError("Le corpus doit contenir au moins un exemple.")
    wers = [wer(str(item.get("reference", "")), str(item.get("hypothesis", ""))) for item in examples]
    cers = [cer(str(item.get("reference", "")), str(item.get("hypothesis", ""))) for item in examples]
    reference_entities = [entity for item in examples for entity in item.get("reference_entities", [])]
    predicted_entities = [entity for item in examples for entity in item.get("predicted_entities", [])]
    pii = entity_metrics(reference_entities, predicted_entities)
    return {
        "examples": len(examples),
        "wer": round(sum(wers) / len(wers), 6),
        "cer": round(sum(cers) / len(cers), 6),
        "pii": pii,
        "method": "normalized_levenshtein_exact_entity_match",
        "warning": "Ces métriques mesurent uniquement le corpus fourni et ne prouvent pas une couverture générale.",
    }

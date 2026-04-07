from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple


LOG_LEVELS = {'info', 'error', 'warn', 'warning', 'debug', 'trace', 'fatal'}
MAX_LEVEL_SCAN_TOKENS = 8

DATE_TOKEN_REGEX = re.compile(r'^\d{6,8}$|^\d{4}-\d{2}-\d{2}$|^\d{4}/\d{2}/\d{2}$')
TIME_TOKEN_REGEX = re.compile(r'^\d{6}$|^\d{2}:\d{2}:\d{2}(?:[.,]\d+)?$')
NUMERIC_ID_REGEX = re.compile(r'^\d+$')
BRACKET_TRIM_REGEX = re.compile(r'^[\[\(\{]+|[\]\)\}]+$')
MULTISPACE_REGEX = re.compile(r'\s+')


@dataclass(frozen=True)
class NormalizationRule:
    pattern: re.Pattern[str]
    replacement: str = '<*>'


DEFAULT_NORMALIZATION_RULES: Tuple[Tuple[str, str], ...] = (
    (r'blk_\d+', '<*>'),
    (r'\b\d{1,3}(?:\.\d{1,3}){3}\b', '<*>'),
    (r'\b0x[0-9a-fA-F]+\b', '<*>'),
    (r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b', '<*>'),
    (r'\b\d+\b', '<*>'),
)


def _strip_brackets(token: str) -> str:
    return BRACKET_TRIM_REGEX.sub('', token)


def _is_log_level_token(token: str) -> bool:
    return _strip_brackets(token).lower() in LOG_LEVELS


def _is_metadata_token(token: str) -> bool:
    cleaned = _strip_brackets(token)
    if _is_log_level_token(cleaned):
        return True
    if DATE_TOKEN_REGEX.fullmatch(cleaned):
        return True
    if TIME_TOKEN_REGEX.fullmatch(cleaned):
        return True
    if NUMERIC_ID_REGEX.fullmatch(cleaned):
        return True
    return False


def _remove_leading_metadata(log: str) -> str:
    tokens = log.strip().split()
    if not tokens:
        return ''

    level_index = -1
    for index, token in enumerate(tokens[:MAX_LEVEL_SCAN_TOKENS]):
        if _is_log_level_token(token):
            level_index = index
            break

    if level_index >= 0:
        return ' '.join(tokens[level_index + 1:]).strip()

    start_index = 0
    while start_index < len(tokens) and start_index < 5 and _is_metadata_token(tokens[start_index]):
        start_index += 1

    return ' '.join(tokens[start_index:]).strip()


def _build_rules(extra_rules: Sequence[Tuple[str, str]] | None = None) -> List[NormalizationRule]:
    rule_pairs: List[Tuple[str, str]] = list(DEFAULT_NORMALIZATION_RULES)
    if extra_rules:
        rule_pairs.extend(extra_rules)

    return [
        NormalizationRule(pattern=re.compile(pattern, flags=re.IGNORECASE), replacement=replacement)
        for pattern, replacement in rule_pairs
    ]


def _apply_normalization_rules(message: str, rules: Iterable[NormalizationRule]) -> str:
    normalized = message
    for rule in rules:
        normalized = rule.pattern.sub(rule.replacement, normalized)
    return normalized


def preprocess_log(
    log: str,
    *,
    enable: bool = True,
    extra_rules: Sequence[Tuple[str, str]] | None = None,
) -> str:
    """Normalize a log line for template extraction.

    Steps:
    1) Remove leading metadata (time/id/level prefixes).
    2) Lowercase normalization.
    3) Replace dynamic values with <*> using reusable regex rules.
    4) Collapse extra spaces.
    """
    if not log:
        return ''

    if not enable:
        return MULTISPACE_REGEX.sub(' ', log).strip()

    stripped = _remove_leading_metadata(log)
    if not stripped:
        return ''

    lowered = stripped.lower()
    normalized = _apply_normalization_rules(lowered, _build_rules(extra_rules=extra_rules))
    return MULTISPACE_REGEX.sub(' ', normalized).strip()

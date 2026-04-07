from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from .template_cache import TemplateCache, TemplateRecord


TOKEN_REGEX = re.compile(r'"[^"]+"|\[[^\]]+\]|\{[^\}]+\}|\S+')
TIMESTAMP_REGEX = re.compile(
    r'\b\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:,\d{3})?\b|\b\d{2}:\d{2}:\d{2}\b'
)
LEVEL_REGEX = re.compile(r'\b(INFO|ERROR|WARN|DEBUG|TRACE|FATAL)\b', re.IGNORECASE)
IP_REGEX = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
UUID_REGEX = re.compile(r'\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b')
HEX_REGEX = re.compile(r'\b0x[0-9a-fA-F]+\b')
NUMERIC_REGEX = re.compile(r'^-?\d+(?:\.\d+)?$')


@dataclass
class DrainMatch:
    template_id: str
    template: str
    confidence: float
    is_new_template: bool
    variables: List[str]


class DrainParser:
    def __init__(self, cache: TemplateCache, similarity_threshold: float = 0.72) -> None:
        self.cache = cache
        self.similarity_threshold = similarity_threshold
        self._length_buckets: Dict[int, List[str]] = {}

    def _tokenize(self, line: str) -> List[str]:
        return TOKEN_REGEX.findall(line.strip())

    def _replace_pattern(self, pattern: re.Pattern, placeholder: str, line: str, variables: List[str]) -> str:
        def replacer(match: re.Match) -> str:
            variables.append(match.group(0))
            return placeholder

        return pattern.sub(replacer, line)

    def extract_timestamp(self, line: str) -> str:
        match = TIMESTAMP_REGEX.search(line)
        return match.group(0) if match else ''

    def extract_level(self, line: str) -> str:
        match = LEVEL_REGEX.search(line)
        return match.group(1).upper() if match else 'UNKNOWN'

    def _normalize_token(self, token: str) -> str:
        if token == '<*>':
            return '<*>'
        if token.startswith('<') and token.endswith('>'):
            return token.lower()
        if UUID_REGEX.fullmatch(token):
            return '<*>'
        if IP_REGEX.fullmatch(token):
            return '<*>'
        if HEX_REGEX.fullmatch(token):
            return '<*>'
        if NUMERIC_REGEX.fullmatch(token):
            return '<*>'
        return token.lower()

    def _template_from_tokens(self, tokens: Iterable[str]) -> Tuple[str, List[str]]:
        normalized_tokens: List[str] = []

        for token in tokens:
            normalized = self._normalize_token(token)
            normalized_tokens.append(normalized)

        return ' '.join(normalized_tokens), []

    def _normalize_line(self, line: str) -> Tuple[str, List[str]]:
        variables: List[str] = []
        normalized = line.strip()
        normalized = self._replace_pattern(TIMESTAMP_REGEX, '<*>', normalized, variables)
        normalized = self._replace_pattern(LEVEL_REGEX, '<*>', normalized, variables)
        normalized = self._replace_pattern(UUID_REGEX, '<*>', normalized, variables)
        normalized = self._replace_pattern(IP_REGEX, '<*>', normalized, variables)
        normalized = self._replace_pattern(HEX_REGEX, '<*>', normalized, variables)
        normalized = self._replace_pattern(NUMERIC_REGEX, '<*>', normalized, variables)
        tokens = self._tokenize(normalized)
        template, _ = self._template_from_tokens(tokens)
        return template, variables

    def _new_template_confidence(self, template: str) -> float:
        if not template:
            return 0.0
        tokens = template.split()
        wildcard_count = tokens.count('<*>')
        if not tokens:
            return 0.0
        wildcard_ratio = wildcard_count / len(tokens)
        return max(0.35, min(0.79, 0.75 - (0.30 * wildcard_ratio)))

    def _jaccard_similarity(self, left: List[str], right: List[str]) -> float:
        left_set = set(left)
        right_set = set(right)
        if not left_set and not right_set:
            return 1.0
        union = left_set | right_set
        if not union:
            return 0.0
        return len(left_set & right_set) / len(union)

    def _prefix_match(self, left: List[str], right: List[str]) -> float:
        if not left or not right:
            return 0.0
        limit = min(3, len(left), len(right))
        matches = sum(1 for index in range(limit) if left[index] == right[index])
        return matches / limit

    def _candidate_template_ids(self, token_count: int) -> List[str]:
        return list(self._length_buckets.get(token_count, []))

    def _score_candidate(self, tokens: List[str], template: str | List[str]) -> float:
        candidate_tokens = template if isinstance(template, list) else template.split()
        jaccard = self._jaccard_similarity(tokens, candidate_tokens)
        prefix = self._prefix_match(tokens, candidate_tokens)
        length_bonus = 1.0 if len(tokens) == len(candidate_tokens) else 0.0
        return (0.6 * jaccard) + (0.25 * prefix) + (0.15 * length_bonus)

    def _register_template(self, record: TemplateRecord) -> None:
        bucket = self._length_buckets.setdefault(len(record.template.split()), [])
        if record.template_id not in bucket:
            bucket.append(record.template_id)

    def update_from_cache(self) -> None:
        self._length_buckets.clear()
        for record in self.cache.list_templates():
            self._register_template(record)

    def learn_template(
        self,
        template: str,
        example_log: str,
        source: str = 'drain',
    ) -> TemplateRecord:
        template_id = hashlib.sha1(template.encode('utf-8')).hexdigest()[:12]
        record = self.cache.add_template(
            template=template,
            template_id=template_id,
            example_log=example_log,
            source=source,
        )
        self._register_template(record)
        return record

    def match(self, line: str) -> Optional[DrainMatch]:
        tokens = self._tokenize(line)
        if not tokens:
            return None

        normalized_tokens, variables = self._template_from_tokens(tokens)
        best_record: Optional[TemplateRecord] = None
        best_score = 0.0

        for template_id in self._candidate_template_ids(len(tokens)):
            record = self.cache.get(template_id)
            if record is None:
                continue

            score = self._score_candidate(normalized_tokens.split(), record.template)
            if score > best_score:
                best_score = score
                best_record = record

        if best_record is not None and best_score >= self.similarity_threshold:
            return DrainMatch(
                template_id=best_record.template_id,
                template=best_record.template,
                confidence=round(best_score, 4),
                is_new_template=False,
                variables=variables,
            )

        synthesized_template, synthesized_variables = self._normalize_line(line)
        if not synthesized_template:
            return None

        template_id = hashlib.sha1(synthesized_template.encode('utf-8')).hexdigest()[:12]
        return DrainMatch(
            template_id=template_id,
            template=synthesized_template,
            confidence=round(max(best_score, self._new_template_confidence(synthesized_template)), 4),
            is_new_template=True,
            variables=synthesized_variables,
        )

    def build_template(self, line: str) -> Tuple[str, List[str]]:
        return self._normalize_line(line)

    def synthesize_match(self, line: str) -> Optional[DrainMatch]:
        return self.match(line)

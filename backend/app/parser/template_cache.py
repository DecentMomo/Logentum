from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass, field
from typing import Dict, List, Optional


def compute_wildcard_ratio(template: str) -> float:
    tokens = template.split()
    if not tokens:
        return 0.0
    wildcard_count = tokens.count('<*>')
    return wildcard_count / len(tokens)


@dataclass
class TemplateRecord:
    template_id: str
    template: str
    count: int = 0
    wildcard_ratio: float = 0.0
    example_logs: List[str] = field(default_factory=list)
    source: str = 'drain'


class TemplateCache:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._templates: Dict[str, TemplateRecord] = {}
        self.llm_calls = 0
        self.new_templates = 0

    def _template_id(self, template: str) -> str:
        return hashlib.sha1(template.encode('utf-8')).hexdigest()[:12]

    def is_empty(self) -> bool:
        with self._lock:
            return not self._templates

    def add_template(
        self,
        template: str,
        *,
        template_id: Optional[str] = None,
        source: str = 'drain',
        example_log: Optional[str] = None,
    ) -> TemplateRecord:
        resolved_id = template_id or self._template_id(template)

        with self._lock:
            record = self._templates.get(resolved_id)
            if record is None:
                record = TemplateRecord(
                    template_id=resolved_id,
                    template=template,
                    count=0,
                    wildcard_ratio=compute_wildcard_ratio(template),
                    source=source,
                )
                self._templates[resolved_id] = record
                self.new_templates += 1

            record.template = template
            record.source = source
            record.wildcard_ratio = compute_wildcard_ratio(template)
            if example_log and example_log not in record.example_logs:
                record.example_logs.append(example_log)
                record.example_logs = record.example_logs[-5:]

            return record

    def update_count(self, template_id: str, increment: int = 1) -> Optional[TemplateRecord]:
        with self._lock:
            record = self._templates.get(template_id)
            if record is None:
                return None
            record.count += max(1, increment)
            return record

    def get_template_stats(self, template_id: str) -> Optional[TemplateRecord]:
        with self._lock:
            return self._templates.get(template_id)

    def get_by_template(self, template: str) -> Optional[TemplateRecord]:
        with self._lock:
            for record in self._templates.values():
                if record.template == template:
                    return record
        return None

    # Backward-compatible alias.
    def get(self, template_id: str) -> Optional[TemplateRecord]:
        return self.get_template_stats(template_id)

    def list_templates(self) -> List[TemplateRecord]:
        with self._lock:
            return sorted(self._templates.values(), key=lambda item: item.count, reverse=True)

    def increment_llm_calls(self) -> None:
        with self._lock:
            self.llm_calls += 1

    def snapshot_metrics(self) -> Dict[str, int]:
        with self._lock:
            return {
                'llm_calls': self.llm_calls,
                'new_templates': self.new_templates,
                'cached_templates': len(self._templates),
            }

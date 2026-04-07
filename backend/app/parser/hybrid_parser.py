from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from typing import Dict, List

from ..config import settings
from .drain_parser import DrainParser
from .llm_parser import LLMParser
from .preprocessing import preprocess_log
from .template_cache import TemplateCache, compute_wildcard_ratio


logger = logging.getLogger(__name__)

MIN_SUPPORT = 5
MAX_WILDCARD_RATIO = 0.6
LLM_BATCH_SIZE = 20
COLD_START_BATCHES = 3


@dataclass
class ParseResult:
    parsed_logs: List[Dict]
    templates: Dict[str, Dict]
    llm_calls: int
    new_templates: int


class HybridParser:
    def __init__(self) -> None:
        self.cache = TemplateCache()
        self.drain_parser = DrainParser(
            cache=self.cache,
            similarity_threshold=settings.drain_similarity_threshold,
        )
        self.llm_parser = LLMParser()
        self._cold_start_batches_sent = 0
        self.drain_parser.update_from_cache()

    def _template_id(self, template: str) -> str:
        return hashlib.sha1(template.encode('utf-8')).hexdigest()[:12]

    def _evaluate_trigger_reason(
        self,
        *,
        is_new_template: bool,
        confidence: float,
        template_count: int,
        wildcard_ratio: float,
    ) -> str | None:
        if self.cache.is_empty() and self._cold_start_batches_sent < COLD_START_BATCHES:
            return 'cold_start'
        if is_new_template:
            return 'new_template'
        if confidence < 0.8:
            return 'low_confidence'
        if template_count < MIN_SUPPORT:
            return 'low_support'
        if wildcard_ratio > MAX_WILDCARD_RATIO:
            return 'over_generalized'
        return None

    def _apply_llm_batch(self, queued_indexes: List[int], parsed_logs: List[Dict]) -> bool:
        if not queued_indexes:
            return False

        batch_logs = [parsed_logs[idx]['processed_line'] for idx in queued_indexes]
        reason_counts: Dict[str, int] = {}
        for idx in queued_indexes:
            reason = parsed_logs[idx].get('trigger_reason', 'unknown')
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

        logger.info('Triggering LLM fallback batch_size=%s reasons=%s', len(batch_logs), reason_counts)

        try:
            llm_templates = self.llm_parser.parse_batch(batch_logs)
        except Exception as error:
            logger.warning('LLM batch failed, using drain fallback templates: %s', error)
            llm_templates = []

        # Keep parser productive even if LLM is unavailable or returns malformed output.
        if not llm_templates or len(llm_templates) != len(batch_logs):
            for batch_offset, global_index in enumerate(queued_indexes):
                fallback_template = parsed_logs[global_index].get('template', '<*>') or '<*>'
                template_id = self._template_id(fallback_template)
                self.cache.add_template(
                    fallback_template,
                    template_id=template_id,
                    source='drain_fallback',
                    example_log=parsed_logs[global_index]['raw_line'],
                )
                self.cache.update_count(template_id)

                record = self.cache.get_template_stats(template_id)
                if record is not None:
                    self.drain_parser._register_template(record)

                parsed_logs[global_index].update(
                    {
                        'template_id': template_id,
                        'template': fallback_template,
                        'confidence': max(float(parsed_logs[global_index].get('confidence', 0.0)), 0.8),
                        'parser': 'drain_fallback',
                    }
                )
            return False

        self.cache.increment_llm_calls()
        self._cold_start_batches_sent += 1

        for batch_offset, template in enumerate(llm_templates):
            global_index = queued_indexes[batch_offset]
            normalized_template = template.strip() or parsed_logs[global_index]['template']
            template_id = self._template_id(normalized_template)
            self.cache.add_template(
                normalized_template,
                template_id=template_id,
                source='llm',
                example_log=parsed_logs[global_index]['raw_line'],
            )
            self.cache.update_count(template_id)

            record = self.cache.get_template_stats(template_id)
            if record is not None:
                self.drain_parser._register_template(record)

            parsed_logs[global_index].update(
                {
                    'template_id': template_id,
                    'template': normalized_template,
                    'confidence': 0.9,
                    'parser': 'llm',
                    'trigger_reason': parsed_logs[global_index].get('trigger_reason', ''),
                }
            )

        return True

    def _parse_with_drain(self, raw_line: str, processed_line: str) -> Dict:
        timestamp = self.drain_parser.extract_timestamp(raw_line)
        log_level = self.drain_parser.extract_level(raw_line)
        match = self.drain_parser.match(processed_line)
        if match is None:
            return {
                'timestamp': timestamp,
                'log_level': log_level,
                'template_id': '',
                'template': '',
                'variables': [],
                'confidence': 0.0,
                'parser': 'unknown',
                'is_new_template': True,
            }

        return {
            'timestamp': timestamp,
            'log_level': log_level,
            'template_id': match.template_id,
            'template': match.template,
            'variables': match.variables,
            'confidence': match.confidence,
            'parser': 'drain',
            'is_new_template': match.is_new_template,
        }

    def parse(self, raw_logs: str) -> ParseResult:
        parsed_logs: List[Dict] = []
        llm_queue: List[int] = []

        for line_number, raw_line in enumerate(raw_logs.splitlines(), start=1):
            clean_line = raw_line.strip()
            if not clean_line:
                continue

            processed_line = preprocess_log(
                clean_line,
                enable=settings.enable_preprocessing,
                extra_rules=settings.get_extra_preprocessing_rules(),
            )
            if not processed_line:
                continue

            parsed_log = self._parse_with_drain(clean_line, processed_line)
            parsed_log['line_number'] = line_number
            parsed_log['raw_line'] = clean_line
            parsed_log['processed_line'] = processed_line
            template = parsed_log.get('template', '')
            template_id = parsed_log.get('template_id') or self._template_id(template)
            parsed_log['template_id'] = template_id

            stats = self.cache.get_template_stats(template_id)
            template_count = stats.count if stats else 0
            wildcard_ratio = stats.wildcard_ratio if stats else compute_wildcard_ratio(template)

            trigger_reason = self._evaluate_trigger_reason(
                is_new_template=bool(parsed_log.get('is_new_template', False)),
                confidence=float(parsed_log.get('confidence', 0.0)),
                template_count=template_count,
                wildcard_ratio=wildcard_ratio,
            )

            if trigger_reason is None:
                self.cache.add_template(
                    template,
                    template_id=template_id,
                    source='drain',
                    example_log=clean_line,
                )
                self.cache.update_count(template_id)
                parsed_log['parser'] = 'drain'
            else:
                parsed_log['trigger_reason'] = trigger_reason
                parsed_log['parser'] = 'llm_pending'

            parsed_logs.append(parsed_log)

            if trigger_reason is not None:
                llm_queue.append(len(parsed_logs) - 1)

            if len(llm_queue) >= LLM_BATCH_SIZE:
                self._apply_llm_batch(llm_queue[:LLM_BATCH_SIZE], parsed_logs)
                llm_queue = llm_queue[LLM_BATCH_SIZE:]

        while llm_queue:
            chunk = llm_queue[:LLM_BATCH_SIZE]
            self._apply_llm_batch(chunk, parsed_logs)
            llm_queue = llm_queue[LLM_BATCH_SIZE:]

        self.drain_parser.update_from_cache()

        templates: Dict[str, Dict] = {}
        for record in self.cache.list_templates():
            templates[record.template_id] = {
                'template': record.template,
                'count': record.count,
                'example_logs': record.example_logs,
                'source': record.source,
                'wildcard_ratio': record.wildcard_ratio,
            }

        metrics = self.cache.snapshot_metrics()

        sanitized_logs = [
            {
                'timestamp': item.get('timestamp', ''),
                'log_level': item.get('log_level', 'UNKNOWN'),
                'template_id': item.get('template_id', ''),
                'template': item.get('template', ''),
                'variables': item.get('variables', []),
                'confidence': item.get('confidence', 0.0),
                'parser': item.get('parser', 'unknown'),
                'line_number': item.get('line_number'),
                'trigger_reason': item.get('trigger_reason'),
            }
            for item in parsed_logs
        ]

        return ParseResult(
            parsed_logs=sanitized_logs,
            templates=templates,
            llm_calls=metrics.get('llm_calls', 0),
            new_templates=metrics.get('new_templates', 0),
        )


_HYBRID_PARSER: HybridParser | None = None


def get_hybrid_parser() -> HybridParser:
    global _HYBRID_PARSER
    if _HYBRID_PARSER is None:
        _HYBRID_PARSER = HybridParser()
    return _HYBRID_PARSER

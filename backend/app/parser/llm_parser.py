from __future__ import annotations

import logging
import re
from typing import Dict, List

import requests

from ..config import settings


logger = logging.getLogger(__name__)

TEMPLATE_LINE_REGEX = re.compile(r'^LogTemplate\[(\d+)\]:\s*`(.+)`\s*$', re.IGNORECASE)
PLACEHOLDER_REGEX = re.compile(r'\{(?:ip|ip_port|blk_id|num|path|hex)\}', re.IGNORECASE)


class LLMParser:
    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.model = settings.openrouter_model
        self.timeout_seconds = settings.llm_timeout_seconds
        self.temperature = settings.llm_temperature

    def available(self) -> bool:
        return bool(self.api_key)

    def _build_prompt(self, logs: List[str]) -> List[Dict[str, str]]:
        injected_logs = '\n'.join(f'Log[{index + 1}]: `{log}`' for index, log in enumerate(logs))
        prompt = f'''
You are an expert in log parsing and log template extraction.

### Task:
You are given multiple log messages. Each log is delimited by backticks.

Your job:
- Identify dynamic variables
- Replace them with meaningful placeholders
- Output structured log templates

---

### Rules:

1. Replace dynamic values with placeholders:
   - IP -> {{ip}}
   - IP:PORT -> {{ip_port}}
   - Block ID (blk_...) -> {{blk_id}}
   - Numbers -> {{num}}
   - File paths -> {{path}}
   - Hex -> {{hex}}

2. DO NOT replace:
   - meaningful words (e.g., "error", "failed", "received")

3. Preserve structure and semantics.

4. Logs with same structure should produce identical templates.

---

### Output Format (STRICT):

For each log:

LogTemplate[1]: `...`
LogTemplate[2]: `...`

NO extra explanation.
NO extra text.

---

### Example:

Log[1]: `Received block blk_-160899 of size 91178 from 10.250.10.6`
Log[2]: `Received block blk_-434451 of size 6710 from 10.250.15.8`

Output:

LogTemplate[1]: `Received block {{blk_id}} of size {{num}} from {{ip}}`
LogTemplate[2]: `Received block {{blk_id}} of size {{num}} from {{ip}}`

---

### INPUT LOGS:

{injected_logs}
'''.strip()
        return [
            {'role': 'system', 'content': 'Return only the requested output format. No explanation.'},
            {'role': 'user', 'content': prompt},
        ]

    def _normalize_template(self, template: str) -> str:
        normalized = PLACEHOLDER_REGEX.sub('<*>', template)
        return re.sub(r'\s+', ' ', normalized).strip()

    def _extract_text(self, response_text: str) -> str:
        cleaned = response_text.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.split('\n', 1)[1]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
        return cleaned.strip()

    def _parse_templates(self, response_text: str, batch_size: int) -> List[str]:
        templates: List[str] = [''] * batch_size
        for line in response_text.splitlines():
            stripped = line.strip()
            match = TEMPLATE_LINE_REGEX.match(stripped)
            if not match:
                continue
            index = int(match.group(1))
            if index < 1 or index > batch_size:
                continue
            templates[index - 1] = self._normalize_template(match.group(2))

        for idx, item in enumerate(templates):
            if not item:
                templates[idx] = '<*>'

        return templates

    def parse_batch(self, logs: List[str]) -> List[str]:
        if not logs:
            return []

        if not self.available():
            logger.warning('OPENROUTER_API_KEY is not configured; skipping LLM fallback')
            return []

        payload = {
            'model': self.model,
            'temperature': self.temperature,
            'messages': self._build_prompt(logs),
        }
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'http://localhost',
            'X-Title': 'Logentum',
        }

        logger.info('Calling OpenRouter for %s logs using model %s', len(logs), self.model)
        response = requests.post(
            self.base_url,
            headers=headers,
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()

        body = response.json()
        content = body['choices'][0]['message']['content']
        parsed_text = self._extract_text(content)
        return self._parse_templates(parsed_text, len(logs))

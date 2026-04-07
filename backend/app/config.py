import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOTENV_PATH = PROJECT_ROOT / '.env'
DOTENV_EXAMPLE_PATH = PROJECT_ROOT.parent / '.env.example'

# Primary source for local secrets.
load_dotenv(dotenv_path=DOTENV_PATH, override=False)

# Backward-compatible fallback when .env is not present.
if not os.getenv('OPENROUTER_API_KEY') and DOTENV_EXAMPLE_PATH.exists():
    load_dotenv(dotenv_path=DOTENV_EXAMPLE_PATH, override=False)


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str = os.getenv('OPENROUTER_API_KEY', '')
    openrouter_base_url: str = os.getenv(
        'OPENROUTER_BASE_URL',
        'https://openrouter.ai/api/v1/chat/completions'
    )
    openrouter_model: str = os.getenv('OPENROUTER_MODEL', 'openai/gpt-oss-20b')
    llm_temperature: float = float(os.getenv('LLM_TEMPERATURE', '0'))
    llm_timeout_seconds: int = int(os.getenv('LLM_TIMEOUT_SECONDS', '90'))
    drain_similarity_threshold: float = float(os.getenv('DRAIN_SIMILARITY_THRESHOLD', '0.72'))
    drain_min_batch_size: int = int(os.getenv('DRAIN_MIN_BATCH_SIZE', '10'))
    drain_max_batch_size: int = int(os.getenv('DRAIN_MAX_BATCH_SIZE', '30'))
    enable_preprocessing: bool = os.getenv('ENABLE_PREPROCESSING', 'true').strip().lower() in {
        '1',
        'true',
        'yes',
        'on',
    }
    preprocessing_extra_rules_json: str = os.getenv('PREPROCESSING_EXTRA_RULES_JSON', '[]')

    def get_extra_preprocessing_rules(self) -> List[Tuple[str, str]]:
        try:
            raw_items = json.loads(self.preprocessing_extra_rules_json)
        except json.JSONDecodeError:
            return []

        parsed_rules: List[Tuple[str, str]] = []
        if not isinstance(raw_items, list):
            return parsed_rules

        for item in raw_items:
            if not isinstance(item, dict):
                continue
            pattern = str(item.get('pattern', '')).strip()
            replacement = str(item.get('replacement', '')).strip()
            if pattern:
                parsed_rules.append((pattern, replacement))

        return parsed_rules


settings = Settings()

from typing import Any, Dict, List

from pydantic import BaseModel


class ParseRequest(BaseModel):
    upload_id: str
    parsing_method: str = 'Drain'


class ParsedLog(BaseModel):
    timestamp: str
    log_level: str
    template_id: str
    template: str
    variables: List[str]
    confidence: float | None = None
    parser: str | None = None
    line_number: int | None = None
    trigger_reason: str | None = None


class ParseResponse(BaseModel):
    parsed_logs: List[ParsedLog]
    templates: Dict[str, Dict[str, Any]]
    llm_calls: int
    new_templates: int


class TemplateItem(BaseModel):
    template_id: str
    template: str
    count: int
    example_logs: List[str]
    source: str
    wildcard_ratio: float


class TemplatesResponse(BaseModel):
    templates: List[TemplateItem]
    metrics: Dict[str, int]


class UploadResponse(BaseModel):
    upload_id: str
    filename: str
    raw_logs: str


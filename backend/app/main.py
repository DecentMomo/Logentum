import uuid
import logging
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .parser import get_hybrid_parser
from .schemas import ParseRequest, ParseResponse, TemplatesResponse, UploadResponse

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / 'uploads'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title='Logentum Parser API', version='1.0.0')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*']
)

hybrid_parser = get_hybrid_parser()


@app.get('/health')
def health_check() -> dict:
    return {'status': 'ok'}


@app.post('/upload', response_model=UploadResponse)
async def upload_log(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=400, detail='Missing file name')

    suffix = Path(file.filename).suffix.lower()
    if suffix not in {'.log', '.txt'}:
        raise HTTPException(status_code=400, detail='Only .log or .txt files are supported')

    upload_id = str(uuid.uuid4())
    target_path = UPLOAD_DIR / f'{upload_id}{suffix}'

    content = await file.read()
    target_path.write_bytes(content)

    decoded_content = content.decode('utf-8', errors='replace')

    logger.info('Uploaded log file %s as %s', file.filename, upload_id)

    return UploadResponse(
        upload_id=upload_id,
        filename=file.filename,
        raw_logs=decoded_content,
    )


@app.post('/parse', response_model=ParseResponse)
def parse_uploaded_logs(request: ParseRequest) -> ParseResponse:
    upload_candidates = list(UPLOAD_DIR.glob(f'{request.upload_id}.*'))

    if not upload_candidates:
        raise HTTPException(status_code=404, detail='Uploaded file not found')

    file_path = upload_candidates[0]
    raw_logs = file_path.read_text(encoding='utf-8', errors='replace')

    result = hybrid_parser.parse(raw_logs)

    logger.info(
        'Parsed upload_id=%s llm_calls=%s new_templates=%s templates=%s',
        request.upload_id,
        result.llm_calls,
        result.new_templates,
        len(result.templates),
    )

    return ParseResponse(
        parsed_logs=result.parsed_logs,
        templates=result.templates,
        llm_calls=result.llm_calls,
        new_templates=result.new_templates,
    )


@app.get('/templates', response_model=TemplatesResponse)
def list_templates() -> TemplatesResponse:
    template_records = hybrid_parser.cache.list_templates()
    templates = [
        {
            'template_id': record.template_id,
            'template': record.template,
            'count': record.count,
            'example_logs': record.example_logs,
            'source': record.source,
            'wildcard_ratio': record.wildcard_ratio,
        }
        for record in template_records
    ]

    return TemplatesResponse(
        templates=templates,
        metrics=hybrid_parser.cache.snapshot_metrics(),
    )

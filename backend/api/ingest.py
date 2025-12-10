from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi import BackgroundTasks
from typing import Optional

from core.pipeline import ingest_source
from models.request_models import IngestRequest
from models.response_models import IngestResponse

router = APIRouter()


@router.post("", response_model=IngestResponse)
async def ingest(
    background_tasks: BackgroundTasks,
    request: IngestRequest,
    file: Optional[UploadFile] = File(default=None),
):
    if not request.source_url and file is None:
        raise HTTPException(status_code=400, detail="Provide either source_url or file.")

    background_tasks.add_task(ingest_source, request=request, file=file)
    return IngestResponse(status="scheduled")

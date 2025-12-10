from fastapi import APIRouter
from models.request_models import QueryRequest
from models.response_models import QueryResponse
from core.pipeline import run_query

router = APIRouter()


@router.post("", response_model=QueryResponse)
async def query(request: QueryRequest):
    result = run_query(request)
    return result

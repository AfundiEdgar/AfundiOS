from fastapi import APIRouter
from db.metadata_store import get_stats
from models.response_models import StatsResponse

router = APIRouter()


@router.get("", response_model=StatsResponse)
def stats():
    return get_stats()

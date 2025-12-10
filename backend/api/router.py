from fastapi import APIRouter

from . import ingest, query, health, stats, conversation, graph, agents, maintenance, briefings

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingestion"])
api_router.include_router(query.router, prefix="/query", tags=["query"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(conversation.router, prefix="/conversation", tags=["conversation"])
api_router.include_router(graph.router, prefix="/graph", tags=["graph"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(maintenance.router, prefix="/maintenance", tags=["maintenance"])
api_router.include_router(briefings.router, prefix="/briefings", tags=["briefings"])

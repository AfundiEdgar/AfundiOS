"""
Graph Visualization API Endpoints

Provides REST endpoints for accessing and analyzing the knowledge graph.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import logging

from backend.core.graph import KnowledgeGraph, GraphBuilder, Node, Edge
from backend.core.graph_analysis import GraphAnalyzer, NodeAnalysis, RelationshipRecommendation
from backend.core.retriever import retrieve_relevant_chunks
from backend.db.metadata_store import get_metadata_store

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])

# Global graph instance
_graph: Optional[KnowledgeGraph] = None
_graph_builder: Optional[GraphBuilder] = None
_graph_analyzer: Optional[GraphAnalyzer] = None


# Response Models
class GraphNodeResponse(BaseModel):
    """Response model for graph nodes."""
    id: str
    text: str
    type: str
    metadata: dict


class GraphEdgeResponse(BaseModel):
    """Response model for graph edges."""
    source: str
    target: str
    weight: float
    type: str


class GraphResponse(BaseModel):
    """Complete graph response."""
    nodes: List[GraphNodeResponse]
    edges: List[GraphEdgeResponse]


class NodeAnalysisResponse(BaseModel):
    """Analysis of a single node."""
    node_id: str
    text: str
    degree: int
    centrality: float
    related_nodes: List[tuple]


class RelationshipRecommendationResponse(BaseModel):
    """Recommended relationship between nodes."""
    source: str
    target: str
    score: float
    reason: str


class GraphStatisticsResponse(BaseModel):
    """Graph statistics."""
    node_count: int
    edge_count: int
    density: float
    avg_degree: float
    clustering_coefficient: float
    connected_components: int
    largest_component_size: int


class TopicsResponse(BaseModel):
    """Topic clusters."""
    clusters: List[List[str]]
    cluster_count: int


async def _ensure_graph_initialized():
    """Initialize graph if needed."""
    global _graph, _graph_builder, _graph_analyzer
    
    if _graph is None:
        logger.info("Initializing knowledge graph...")
        _graph = KnowledgeGraph()
        _graph_builder = GraphBuilder(similarity_threshold=0.6)
        _graph_analyzer = GraphAnalyzer(_graph)
        
        # Load chunks from metadata store and build graph
        try:
            metadata_store = get_metadata_store()
            chunks = metadata_store.get_all_documents()
            
            if chunks:
                # Convert to chunk format expected by graph builder
                chunk_dicts = [
                    {
                        "id": chunk.get("id", f"chunk_{i}"),
                        "text": chunk.get("content", ""),
                        "metadata": {
                            "source": chunk.get("source", ""),
                            "doc_id": chunk.get("doc_id", ""),
                        }
                    }
                    for i, chunk in enumerate(chunks)
                ]
                
                _graph = _graph_builder.build_from_chunks(chunk_dicts)
                _graph_analyzer = GraphAnalyzer(_graph)
                logger.info(f"Graph initialized with {len(chunks)} chunks")
        except Exception as e:
            logger.error(f"Error initializing graph: {e}")
            _graph = KnowledgeGraph()
            _graph_analyzer = GraphAnalyzer(_graph)


@router.get("/initialize", summary="Initialize or rebuild the knowledge graph")
async def initialize_graph():
    """Reinitialize the knowledge graph from stored data."""
    global _graph, _graph_builder, _graph_analyzer
    
    _graph = None
    _graph_builder = None
    _graph_analyzer = None
    
    await _ensure_graph_initialized()
    
    stats = _graph.calculate_statistics()
    return {
        "status": "initialized",
        "nodes": stats.node_count,
        "edges": stats.edge_count,
        "components": stats.connected_components,
    }


@router.get("/nodes", response_model=List[GraphNodeResponse], summary="Get all graph nodes")
async def get_nodes(
    node_type: Optional[str] = Query(None, description="Filter by node type"),
):
    """Retrieve all nodes in the knowledge graph."""
    await _ensure_graph_initialized()
    
    nodes = []
    for node in _graph.nodes.values():
        if node_type and node.type != node_type:
            continue
        nodes.append(
            GraphNodeResponse(
                id=node.id,
                text=node.text,
                type=node.type,
                metadata=node.metadata,
            )
        )
    
    return nodes


@router.get("/edges", response_model=List[GraphEdgeResponse], summary="Get all graph edges")
async def get_edges(
    min_weight: float = Query(0.0, description="Minimum edge weight"),
):
    """Retrieve all edges in the knowledge graph."""
    await _ensure_graph_initialized()
    
    edges = []
    for edge in _graph.edges:
        if edge.weight < min_weight:
            continue
        edges.append(
            GraphEdgeResponse(
                source=edge.source,
                target=edge.target,
                weight=edge.weight,
                type=edge.relationship_type,
            )
        )
    
    return edges


@router.get("", response_model=GraphResponse, summary="Get complete graph")
async def get_graph():
    """Retrieve the complete knowledge graph."""
    await _ensure_graph_initialized()
    
    nodes = [
        GraphNodeResponse(
            id=node.id,
            text=node.text,
            type=node.type,
            metadata=node.metadata,
        )
        for node in _graph.nodes.values()
    ]
    
    edges = [
        GraphEdgeResponse(
            source=edge.source,
            target=edge.target,
            weight=edge.weight,
            type=edge.relationship_type,
        )
        for edge in _graph.edges
    ]
    
    return GraphResponse(nodes=nodes, edges=edges)


@router.get("/statistics", response_model=GraphStatisticsResponse, summary="Get graph statistics")
async def get_statistics():
    """Get statistical information about the graph."""
    await _ensure_graph_initialized()
    
    stats = _graph.calculate_statistics()
    return GraphStatisticsResponse(
        node_count=stats.node_count,
        edge_count=stats.edge_count,
        density=stats.density,
        avg_degree=stats.avg_degree,
        clustering_coefficient=stats.clustering_coefficient,
        connected_components=stats.connected_components,
        largest_component_size=stats.largest_component_size,
    )


@router.get("/nodes/{node_id}/analysis", summary="Analyze a specific node")
async def analyze_node(node_id: str):
    """Get detailed analysis of a node."""
    await _ensure_graph_initialized()
    
    analysis = _graph_analyzer.analyze_node(node_id)
    if not analysis:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    return analysis.to_dict()


@router.get("/nodes/{node_id}/neighbors", summary="Get node neighbors")
async def get_node_neighbors(
    node_id: str,
    distance: int = Query(1, ge=1, le=5, description="Search distance"),
):
    """Get all neighbors of a node up to specified distance."""
    await _ensure_graph_initialized()
    
    if node_id not in _graph.nodes:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    neighbors = _graph.get_node_neighbors(node_id, distance=distance)
    return [
        GraphNodeResponse(
            id=node.id,
            text=node.text,
            type=node.type,
            metadata=node.metadata,
        )
        for node in neighbors.values()
    ]


@router.get("/nodes/{node_id}/similar", summary="Find similar nodes")
async def get_similar_nodes(
    node_id: str,
    limit: int = Query(5, ge=1, le=20),
    min_weight: float = Query(0.0, ge=0.0, le=1.0),
):
    """Find nodes most similar to the given node."""
    await _ensure_graph_initialized()
    
    similar = _graph_analyzer.find_similar_nodes(node_id, limit=limit, min_weight=min_weight)
    return [
        {
            "node_id": node.id,
            "text": node.text[:100] + "..." if len(node.text) > 100 else node.text,
            "similarity": weight,
        }
        for node, weight in similar
    ]


@router.get("/key-nodes", summary="Find most important nodes")
async def get_key_nodes(top_k: int = Query(5, ge=1, le=20)):
    """Find the most important nodes in the graph."""
    await _ensure_graph_initialized()
    
    key_nodes = _graph_analyzer.find_key_nodes(top_k=top_k)
    return [node.to_dict() for node in key_nodes]


@router.get("/topics", response_model=TopicsResponse, summary="Get topic clusters")
async def get_topics():
    """Find topic clusters in the knowledge graph."""
    await _ensure_graph_initialized()
    
    clusters = _graph_analyzer.find_topic_clusters(min_cluster_size=2)
    return TopicsResponse(clusters=clusters, cluster_count=len(clusters))


@router.get("/recommendations", summary="Get relationship recommendations")
async def get_recommendations(limit: int = Query(10, ge=1, le=50)):
    """Get recommended relationships that should be added."""
    await _ensure_graph_initialized()
    
    recommendations = _graph_analyzer.recommend_connections(limit=limit)
    return [rec.to_dict() for rec in recommendations]


@router.get("/paths/{source}/to/{target}", summary="Find path between nodes")
async def find_path(source: str, target: str):
    """Find the shortest path between two nodes."""
    await _ensure_graph_initialized()
    
    if source not in _graph.nodes or target not in _graph.nodes:
        raise HTTPException(status_code=404, detail="Source or target node not found")
    
    path = _graph_analyzer.get_path_between(source, target)
    if not path:
        return {"path": None, "length": None}
    
    return {
        "path": path,
        "length": len(path) - 1,
        "nodes": [
            {
                "id": nid,
                "text": _graph.nodes[nid].text[:100] + "..."
                if len(_graph.nodes[nid].text) > 100
                else _graph.nodes[nid].text,
            }
            for nid in path
        ],
    }


@router.get("/subgraph/{node_id}", summary="Get subgraph around node")
async def get_subgraph(
    node_id: str,
    distance: int = Query(2, ge=1, le=5),
):
    """Extract subgraph centered around a node."""
    await _ensure_graph_initialized()
    
    if node_id not in _graph.nodes:
        raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
    
    subgraph = _graph_analyzer.get_subgraph_around_node(node_id, distance=distance)
    
    nodes = [
        GraphNodeResponse(
            id=node.id,
            text=node.text,
            type=node.type,
            metadata=node.metadata,
        )
        for node in subgraph.nodes.values()
    ]
    
    edges = [
        GraphEdgeResponse(
            source=edge.source,
            target=edge.target,
            weight=edge.weight,
            type=edge.relationship_type,
        )
        for edge in subgraph.edges
    ]
    
    return GraphResponse(nodes=nodes, edges=edges)


@router.post("/search", summary="Search graph by text")
async def search_graph(
    query: str,
    limit: int = Query(10, ge=1, le=50),
):
    """Find nodes related to a text query."""
    await _ensure_graph_initialized()
    
    # Use retriever to find relevant chunks
    try:
        results = retrieve_relevant_chunks(query, k=limit, enable_rerank=True)
        
        matching_nodes = []
        for result in results:
            node_id = result.get("id")
            if node_id and node_id in _graph.nodes:
                node = _graph.nodes[node_id]
                matching_nodes.append(
                    GraphNodeResponse(
                        id=node.id,
                        text=node.text,
                        type=node.type,
                        metadata=node.metadata,
                    )
                )
        
        return {
            "query": query,
            "nodes": matching_nodes,
            "count": len(matching_nodes),
        }
    except Exception as e:
        logger.error(f"Error searching graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))

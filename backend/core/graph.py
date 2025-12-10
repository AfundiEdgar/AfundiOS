"""
Graph-Based Memory Visualization

Builds and analyzes knowledge graphs from document chunks and relationships.
Identifies connections between documents, semantic clusters, and key concepts.
"""

from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass, field, asdict
import logging
from collections import defaultdict
import json

logger = logging.getLogger(__name__)


@dataclass
class Node:
    """Represents a chunk or document in the knowledge graph."""
    id: str
    text: str
    type: str = "chunk"  # "chunk" or "document"
    metadata: Dict = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    
    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text[:100] + "..." if len(self.text) > 100 else self.text,
            "type": self.type,
            "metadata": self.metadata,
        }


@dataclass
class Edge:
    """Represents a relationship between nodes."""
    source: str
    target: str
    weight: float = 1.0
    relationship_type: str = "related"  # "similar", "mentioned", "related", "hierarchical"
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "source": self.source,
            "target": self.target,
            "weight": self.weight,
            "type": self.relationship_type,
            "metadata": self.metadata,
        }


@dataclass
class GraphStatistics:
    """Statistics about the knowledge graph."""
    node_count: int
    edge_count: int
    density: float  # edge_count / max_possible_edges
    avg_degree: float
    clustering_coefficient: float
    connected_components: int
    largest_component_size: int
    most_connected_node: Optional[Tuple[str, int]] = None
    most_similar_pairs: List[Tuple[str, str, float]] = field(default_factory=list)
    
    def to_dict(self):
        return asdict(self)


class KnowledgeGraph:
    """Builds and maintains a knowledge graph from document chunks."""
    
    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.edges: List[Edge] = []
        self.adjacency: Dict[str, Set[str]] = defaultdict(set)
        
    def add_node(self, node: Node) -> None:
        """Add a node to the graph."""
        self.nodes[node.id] = node
        if node.id not in self.adjacency:
            self.adjacency[node.id] = set()
    
    def add_edge(self, edge: Edge) -> None:
        """Add an edge to the graph."""
        if edge.source not in self.nodes or edge.target not in self.nodes:
            logger.warning(f"Edge references non-existent nodes: {edge.source} -> {edge.target}")
            return
        
        self.edges.append(edge)
        self.adjacency[edge.source].add(edge.target)
        self.adjacency[edge.target].add(edge.source)  # Undirected
    
    def get_node_neighbors(self, node_id: str, distance: int = 1) -> Dict[str, Node]:
        """Get all neighbors of a node up to specified distance."""
        neighbors = {}
        visited = set()
        frontier = {node_id}
        
        for _ in range(distance):
            next_frontier = set()
            for current_id in frontier:
                if current_id in visited:
                    continue
                visited.add(current_id)
                
                for neighbor_id in self.adjacency.get(current_id, set()):
                    if neighbor_id not in visited:
                        next_frontier.add(neighbor_id)
                        neighbors[neighbor_id] = self.nodes[neighbor_id]
            
            frontier = next_frontier
        
        return neighbors
    
    def get_edges_for_node(self, node_id: str) -> List[Edge]:
        """Get all edges connected to a node."""
        return [e for e in self.edges if e.source == node_id or e.target == node_id]
    
    def get_connected_components(self) -> List[Set[str]]:
        """Find connected components using DFS."""
        visited = set()
        components = []
        
        def dfs(node_id: str, component: Set[str]):
            visited.add(node_id)
            component.add(node_id)
            for neighbor in self.adjacency.get(node_id, set()):
                if neighbor not in visited:
                    dfs(neighbor, component)
        
        for node_id in self.nodes:
            if node_id not in visited:
                component: Set[str] = set()
                dfs(node_id, component)
                components.append(component)
        
        return sorted(components, key=len, reverse=True)
    
    def calculate_statistics(self) -> GraphStatistics:
        """Calculate graph statistics."""
        node_count = len(self.nodes)
        edge_count = len(self.edges)
        
        # Density
        max_edges = node_count * (node_count - 1) / 2 if node_count > 1 else 0
        density = edge_count / max_edges if max_edges > 0 else 0.0
        
        # Average degree
        degrees = [len(neighbors) for neighbors in self.adjacency.values()]
        avg_degree = sum(degrees) / len(degrees) if degrees else 0.0
        
        # Clustering coefficient (simplified)
        clustering_coeff = self._calculate_clustering_coefficient()
        
        # Connected components
        components = self.get_connected_components()
        connected_components = len(components)
        largest_component = len(components[0]) if components else 0
        
        # Most connected node
        most_connected = None
        if degrees:
            max_degree = max(degrees)
            for node_id, neighbors in self.adjacency.items():
                if len(neighbors) == max_degree:
                    most_connected = (node_id, max_degree)
                    break
        
        # Most similar pairs (top weighted edges)
        most_similar = sorted(
            [(e.source, e.target, e.weight) for e in self.edges],
            key=lambda x: x[2],
            reverse=True
        )[:10]
        
        return GraphStatistics(
            node_count=node_count,
            edge_count=edge_count,
            density=density,
            avg_degree=avg_degree,
            clustering_coefficient=clustering_coeff,
            connected_components=connected_components,
            largest_component_size=largest_component,
            most_connected_node=most_connected,
            most_similar_pairs=most_similar,
        )
    
    def _calculate_clustering_coefficient(self) -> float:
        """Calculate clustering coefficient."""
        coefficients = []
        
        for node_id, neighbors in self.adjacency.items():
            if len(neighbors) < 2:
                continue
            
            # Count edges between neighbors
            edges_between = 0
            neighbors_list = list(neighbors)
            for i, n1 in enumerate(neighbors_list):
                for n2 in neighbors_list[i+1:]:
                    if n2 in self.adjacency.get(n1, set()):
                        edges_between += 1
            
            # Max possible edges between neighbors
            max_edges = len(neighbors) * (len(neighbors) - 1) / 2
            if max_edges > 0:
                coeff = edges_between / max_edges
                coefficients.append(coeff)
        
        return sum(coefficients) / len(coefficients) if coefficients else 0.0
    
    def find_semantic_clusters(self, similarity_threshold: float = 0.7) -> List[List[str]]:
        """Find clusters of semantically similar chunks."""
        # Simple community detection: groupby edge weights
        clusters = []
        visited = set()
        
        for node_id in self.nodes:
            if node_id in visited:
                continue
            
            cluster = {node_id}
            visited.add(node_id)
            frontier = {node_id}
            
            while frontier:
                current = frontier.pop()
                for edge in self.get_edges_for_node(current):
                    neighbor = edge.target if edge.source == current else edge.source
                    if neighbor not in visited and edge.weight >= similarity_threshold:
                        cluster.add(neighbor)
                        visited.add(neighbor)
                        frontier.add(neighbor)
            
            if len(cluster) > 1:
                clusters.append(sorted(list(cluster)))
        
        return clusters
    
    def to_dict(self) -> Dict:
        """Convert graph to dictionary format."""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges],
        }
    
    def to_json(self) -> str:
        """Convert graph to JSON."""
        return json.dumps(self.to_dict(), indent=2)


class GraphBuilder:
    """Builds knowledge graphs from document chunks and embeddings."""
    
    def __init__(self, similarity_threshold: float = 0.6):
        self.similarity_threshold = similarity_threshold
        self.graph = KnowledgeGraph()
    
    def build_from_chunks(
        self,
        chunks: List[Dict],
        embeddings: Optional[List[List[float]]] = None,
    ) -> KnowledgeGraph:
        """Build graph from chunks with optional embeddings."""
        # Add nodes
        for i, chunk in enumerate(chunks):
            node = Node(
                id=chunk.get("id", f"chunk_{i}"),
                text=chunk.get("text", ""),
                type="chunk",
                metadata=chunk.get("metadata", {}),
                embedding=embeddings[i] if embeddings else None,
            )
            self.graph.add_node(node)
        
        # Build edges based on similarity
        if embeddings:
            self._build_edges_from_embeddings(embeddings, chunks)
        else:
            self._build_edges_from_text(chunks)
        
        return self.graph
    
    def _build_edges_from_embeddings(
        self,
        embeddings: List[List[float]],
        chunks: List[Dict],
    ) -> None:
        """Build edges using cosine similarity of embeddings."""
        from math import sqrt
        
        def cosine_similarity(v1, v2):
            dot = sum(a * b for a, b in zip(v1, v2))
            mag1 = sqrt(sum(a * a for a in v1))
            mag2 = sqrt(sum(b * b for b in v2))
            if mag1 == 0 or mag2 == 0:
                return 0
            return dot / (mag1 * mag2)
        
        # Create edges between similar chunks
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                similarity = cosine_similarity(embeddings[i], embeddings[j])
                
                if similarity >= self.similarity_threshold:
                    edge = Edge(
                        source=chunks[i].get("id", f"chunk_{i}"),
                        target=chunks[j].get("id", f"chunk_{j}"),
                        weight=similarity,
                        relationship_type="similar",
                    )
                    self.graph.add_edge(edge)
    
    def _build_edges_from_text(self, chunks: List[Dict]) -> None:
        """Build edges using text-based similarity (keyword matching)."""
        # Extract keywords from each chunk
        keywords_per_chunk = []
        for chunk in chunks:
            text = chunk.get("text", "").lower()
            # Simple keyword extraction (words > 3 chars)
            words = set(w for w in text.split() if len(w) > 3)
            keywords_per_chunk.append(words)
        
        # Create edges based on keyword overlap
        for i in range(len(chunks)):
            for j in range(i + 1, len(chunks)):
                if not keywords_per_chunk[i] or not keywords_per_chunk[j]:
                    continue
                
                overlap = keywords_per_chunk[i] & keywords_per_chunk[j]
                max_keywords = max(len(keywords_per_chunk[i]), len(keywords_per_chunk[j]))
                
                similarity = len(overlap) / max_keywords if max_keywords > 0 else 0
                
                if similarity >= self.similarity_threshold:
                    edge = Edge(
                        source=chunks[i].get("id", f"chunk_{i}"),
                        target=chunks[j].get("id", f"chunk_{j}"),
                        weight=similarity,
                        relationship_type="similar",
                    )
                    self.graph.add_edge(edge)
    
    def add_document_hierarchy(self, doc_chunks: Dict[str, List[str]]) -> None:
        """Add hierarchical edges between chunks of same document."""
        for doc_id, chunk_ids in doc_chunks.items():
            # Add edges between consecutive chunks
            for i in range(len(chunk_ids) - 1):
                edge = Edge(
                    source=chunk_ids[i],
                    target=chunk_ids[i + 1],
                    weight=0.9,  # High weight for sequential relationship
                    relationship_type="hierarchical",
                    metadata={"document": doc_id, "sequential": True},
                )
                self.graph.add_edge(edge)
    
    def add_mention_edges(self, chunk_mentions: Dict[str, List[str]]) -> None:
        """Add edges for chunk mentions (references) between chunks."""
        for source_chunk, mentioned_chunks in chunk_mentions.items():
            for target_chunk in mentioned_chunks:
                if source_chunk in self.graph.nodes and target_chunk in self.graph.nodes:
                    edge = Edge(
                        source=source_chunk,
                        target=target_chunk,
                        weight=0.8,
                        relationship_type="mentioned",
                        metadata={"explicit_reference": True},
                    )
                    self.graph.add_edge(edge)

"""
Graph Analysis and Relationship Discovery

Provides analysis utilities for finding related documents, key nodes,
and semantic clusters within the knowledge graph.
"""

from typing import List, Dict, Set, Tuple, Optional
import logging
from dataclasses import dataclass, field, asdict

from backend.core.graph import KnowledgeGraph, Node, Edge

logger = logging.getLogger(__name__)


@dataclass
class NodeAnalysis:
    """Analysis results for a single node."""
    node_id: str
    node_text: str
    degree: int
    betweenness_centrality: float = 0.0
    closeness_centrality: float = 0.0
    clustering_coefficient: float = 0.0
    importance_score: float = 0.0
    related_nodes: List[Tuple[str, float]] = field(default_factory=list)  # (node_id, weight)
    
    def to_dict(self):
        return {
            "node_id": self.node_id,
            "text": self.node_text[:100] + "..." if len(self.node_text) > 100 else self.node_text,
            "degree": self.degree,
            "centrality": self.importance_score,
            "related_nodes": self.related_nodes,
        }


@dataclass
class RelationshipRecommendation:
    """Recommendation for a relationship that should exist but doesn't."""
    source: str
    target: str
    score: float
    reason: str
    
    def to_dict(self):
        return asdict(self)


class GraphAnalyzer:
    """Analyzes knowledge graphs for relationships and patterns."""
    
    def __init__(self, graph: KnowledgeGraph):
        self.graph = graph
        self._node_analysis_cache: Dict[str, NodeAnalysis] = {}
    
    def analyze_node(self, node_id: str) -> Optional[NodeAnalysis]:
        """Analyze properties of a single node."""
        if node_id not in self.graph.nodes:
            return None
        
        if node_id in self._node_analysis_cache:
            return self._node_analysis_cache[node_id]
        
        node = self.graph.nodes[node_id]
        neighbors = self.graph.get_node_neighbors(node_id, distance=1)
        neighbor_ids = list(neighbors.keys())
        
        # Calculate metrics
        degree = len(neighbor_ids)
        betweenness = self._calculate_betweenness_centrality(node_id)
        closeness = self._calculate_closeness_centrality(node_id)
        clustering_coeff = self._calculate_node_clustering_coefficient(node_id)
        
        # Importance score (weighted combination)
        importance = (
            0.4 * (degree / max(len(self.graph.nodes), 1)) +
            0.3 * betweenness +
            0.2 * closeness +
            0.1 * clustering_coeff
        )
        
        # Get related nodes with weights
        related = self._get_weighted_neighbors(node_id)
        
        analysis = NodeAnalysis(
            node_id=node_id,
            node_text=node.text,
            degree=degree,
            betweenness_centrality=betweenness,
            closeness_centrality=closeness,
            clustering_coefficient=clustering_coeff,
            importance_score=importance,
            related_nodes=related,
        )
        
        self._node_analysis_cache[node_id] = analysis
        return analysis
    
    def find_similar_nodes(
        self,
        node_id: str,
        limit: int = 5,
        min_weight: float = 0.0,
    ) -> List[Tuple[Node, float]]:
        """Find nodes similar to the given node."""
        if node_id not in self.graph.nodes:
            return []
        
        similar = []
        for edge in self.graph.get_edges_for_node(node_id):
            if edge.weight < min_weight:
                continue
            
            other_id = edge.target if edge.source == node_id else edge.source
            node = self.graph.nodes[other_id]
            similar.append((node, edge.weight))
        
        return sorted(similar, key=lambda x: x[1], reverse=True)[:limit]
    
    def find_key_nodes(self, top_k: int = 5) -> List[NodeAnalysis]:
        """Find most important nodes in the graph."""
        analyses = []
        for node_id in self.graph.nodes:
            analysis = self.analyze_node(node_id)
            if analysis:
                analyses.append(analysis)
        
        return sorted(analyses, key=lambda a: a.importance_score, reverse=True)[:top_k]
    
    def find_topic_clusters(self, min_cluster_size: int = 2) -> List[List[str]]:
        """Find thematic clusters of related nodes."""
        return self.graph.find_semantic_clusters(similarity_threshold=0.6)
    
    def recommend_connections(self, limit: int = 10) -> List[RelationshipRecommendation]:
        """Recommend missing connections between nodes."""
        recommendations = []
        
        # Look for paths of length 2 where no direct edge exists
        for node_id in self.graph.nodes:
            neighbors = self.graph.adjacency[node_id]
            for neighbor in neighbors:
                for potential_target in self.graph.adjacency.get(neighbor, set()):
                    if (
                        potential_target == node_id or
                        potential_target in neighbors or
                        potential_target not in self.graph.nodes
                    ):
                        continue
                    
                    # Score based on common neighbors
                    common_neighbors = (
                        self.graph.adjacency[node_id] &
                        self.graph.adjacency[potential_target]
                    )
                    score = len(common_neighbors) * 0.5
                    
                    if score > 0:
                        recommendations.append(
                            RelationshipRecommendation(
                                source=node_id,
                                target=potential_target,
                                score=score,
                                reason=f"Shared {len(common_neighbors)} common neighbors",
                            )
                        )
        
        return sorted(recommendations, key=lambda r: r.score, reverse=True)[:limit]
    
    def get_path_between(self, source: str, target: str) -> Optional[List[str]]:
        """Find shortest path between two nodes using BFS."""
        if source not in self.graph.nodes or target not in self.graph.nodes:
            return None
        
        if source == target:
            return [source]
        
        from collections import deque
        
        queue = deque([(source, [source])])
        visited = {source}
        
        while queue:
            current, path = queue.popleft()
            
            for neighbor in self.graph.adjacency.get(current, set()):
                if neighbor == target:
                    return path + [neighbor]
                
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None
    
    def get_subgraph_around_node(
        self,
        node_id: str,
        distance: int = 2,
    ) -> KnowledgeGraph:
        """Extract subgraph around a node."""
        from backend.core.graph import KnowledgeGraph
        
        subgraph = KnowledgeGraph()
        
        # Get all nodes within distance
        nodes_to_include = {node_id}
        for _ in range(distance):
            new_nodes = set()
            for current in nodes_to_include:
                new_nodes.update(self.graph.adjacency.get(current, set()))
            nodes_to_include.update(new_nodes)
        
        # Add nodes
        for nid in nodes_to_include:
            if nid in self.graph.nodes:
                subgraph.add_node(self.graph.nodes[nid])
        
        # Add edges
        for edge in self.graph.edges:
            if edge.source in nodes_to_include and edge.target in nodes_to_include:
                subgraph.add_edge(edge)
        
        return subgraph
    
    def _calculate_betweenness_centrality(self, node_id: str) -> float:
        """Calculate betweenness centrality (simplified)."""
        # Simplified: count how many shortest paths go through this node
        paths_through = 0
        total_paths = 0
        
        node_ids = list(self.graph.nodes.keys())
        for source in node_ids:
            for target in node_ids:
                if source >= target:
                    continue
                
                path = self.get_path_between(source, target)
                if path:
                    total_paths += 1
                    if node_id in path[1:-1]:  # Exclude source and target
                        paths_through += 1
        
        return paths_through / max(total_paths, 1)
    
    def _calculate_closeness_centrality(self, node_id: str) -> float:
        """Calculate closeness centrality (simplified)."""
        if node_id not in self.graph.nodes:
            return 0.0
        
        distances = []
        for other_id in self.graph.nodes:
            if other_id == node_id:
                continue
            
            path = self.get_path_between(node_id, other_id)
            if path:
                distances.append(len(path) - 1)
            else:
                distances.append(float('inf'))
        
        if not distances or all(d == float('inf') for d in distances):
            return 0.0
        
        valid_distances = [d for d in distances if d != float('inf')]
        if not valid_distances:
            return 0.0
        
        avg_distance = sum(valid_distances) / len(valid_distances)
        return 1.0 / (1.0 + avg_distance)
    
    def _calculate_node_clustering_coefficient(self, node_id: str) -> float:
        """Calculate clustering coefficient for a node."""
        neighbors = list(self.graph.adjacency.get(node_id, set()))
        
        if len(neighbors) < 2:
            return 0.0
        
        # Count edges between neighbors
        edges_between = 0
        for i, n1 in enumerate(neighbors):
            for n2 in neighbors[i + 1:]:
                if n2 in self.graph.adjacency.get(n1, set()):
                    edges_between += 1
        
        # Max possible edges
        max_edges = len(neighbors) * (len(neighbors) - 1) / 2
        return edges_between / max_edges if max_edges > 0 else 0.0
    
    def _get_weighted_neighbors(self, node_id: str) -> List[Tuple[str, float]]:
        """Get neighbors with edge weights."""
        neighbors = []
        for edge in self.graph.get_edges_for_node(node_id):
            other_id = edge.target if edge.source == node_id else edge.source
            neighbors.append((other_id, edge.weight))
        
        return sorted(neighbors, key=lambda x: x[1], reverse=True)

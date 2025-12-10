"""
Quick test to verify graph module implementation.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    # Test imports
    from backend.core.graph import (
        Node, Edge, KnowledgeGraph, GraphBuilder, GraphStatistics
    )
    from backend.core.graph_analysis import (
        GraphAnalyzer, NodeAnalysis, RelationshipRecommendation
    )
    
    print("✓ Graph modules imported successfully")
    
    # Test basic graph creation
    graph = KnowledgeGraph()
    node1 = Node(id="chunk_1", text="Machine learning basics", type="chunk")
    node2 = Node(id="chunk_2", text="Deep learning fundamentals", type="chunk")
    
    graph.add_node(node1)
    graph.add_node(node2)
    
    edge = Edge(source="chunk_1", target="chunk_2", weight=0.75, relationship_type="similar")
    graph.add_edge(edge)
    
    print(f"✓ Created graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
    
    # Test graph analyzer
    analyzer = GraphAnalyzer(graph)
    stats = graph.calculate_statistics()
    
    print(f"✓ Graph statistics calculated: density={stats.density:.3f}, avg_degree={stats.avg_degree:.2f}")
    
    # Test node analysis
    analysis = analyzer.analyze_node("chunk_1")
    print(f"✓ Node analysis: degree={analysis.degree}, centrality={analysis.importance_score:.3f}")
    
    # Test graph builder with sample data
    chunks = [
        {"id": "c1", "text": "Introduction to machine learning", "metadata": {}},
        {"id": "c2", "text": "Machine learning algorithms", "metadata": {}},
        {"id": "c3", "text": "Deep learning neural networks", "metadata": {}},
    ]
    
    builder = GraphBuilder(similarity_threshold=0.5)
    built_graph = builder.build_from_chunks(chunks)
    
    print(f"✓ Built graph from chunks: {len(built_graph.nodes)} nodes")
    
    print("\n✅ All graph module tests passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

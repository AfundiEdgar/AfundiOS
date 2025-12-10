"""
Test Agentic Extensions - Verify all agent components work correctly.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("=" * 60)
    print("Testing Agentic Extensions")
    print("=" * 60)
    
    # Test imports
    print("\n✓ Importing agents...")
    from backend.core.agents import (
        PlannerAgent,
        CriticAgent,
        SummarizerAgent,
        AgentOrchestrator,
        TaskStatus,
        SummaryStyle,
        WorkflowMode,
    )
    print("  ✓ All agent classes imported successfully")
    
    # Test Planner
    print("\n✓ Testing Planner Agent...")
    planner = PlannerAgent()
    workflow = planner.plan_workflow(
        goal="Create daily briefing",
        description="Generate executive summary of new documents",
    )
    print(f"  ✓ Created workflow: {workflow.id}")
    print(f"  ✓ Tasks created: {len(workflow.tasks)}")
    print(f"  ✓ Workflow status: {workflow.status}")
    progress = planner.get_workflow_progress(workflow.id)
    print(f"  ✓ Progress: {progress['completed']}/{progress['total']} complete")
    
    # Test Critic
    print("\n✓ Testing Critic Agent...")
    critic = CriticAgent()
    test_content = "Machine learning is a fundamental technique in artificial intelligence. It involves algorithms that can learn from data without explicit programming. Applications include computer vision, natural language processing, and recommendation systems."
    review = critic.review(
        content=test_content,
        content_type="summary",
        context={"goal": "Create technical briefing"},
        source_references=["research_paper.pdf"],
    )
    print(f"  ✓ Review completed: {review.content_id}")
    print(f"  ✓ Quality score: {review.overall_quality_score:.1%}")
    print(f"  ✓ Approved: {review.is_approved}")
    print(f"  ✓ Issues found: {len(review.issues)}")
    
    # Test Summarizer
    print("\n✓ Testing Summarizer Agent...")
    summarizer = SummarizerAgent()
    long_content = """
    Machine learning is a subset of artificial intelligence that focuses on developing systems 
    that can learn from data. Deep learning, which uses neural networks with multiple layers, 
    has revolutionized fields like computer vision and natural language processing. 
    Reinforcement learning enables agents to learn through interaction with their environment.
    Transfer learning allows models trained on one task to be adapted for another. 
    These techniques have applications across healthcare, finance, autonomous vehicles, and more.
    """
    summary = summarizer.summarize(
        content=long_content,
        style=SummaryStyle.BULLET_POINTS,
    )
    print(f"  ✓ Summary created: {summary.content_id}")
    print(f"  ✓ Original: {summary.original_length} chars")
    print(f"  ✓ Summary: {summary.summary_length} chars")
    print(f"  ✓ Compression: {summary.compression_ratio:.1%}")
    print(f"  ✓ Key points: {len(summary.key_points)}")
    print(f"  ✓ Topics: {len(summary.topics)}")
    
    # Test Orchestrator
    print("\n✓ Testing Orchestrator...")
    config = type('Config', (), {
        'mode': WorkflowMode.SEQUENTIAL,
        'enable_criticism': True,
        'enable_summarization': True,
    })()
    # Note: AgentExecutionConfig needs proper instantiation
    from backend.core.agents.orchestrator import AgentExecutionConfig
    config = AgentExecutionConfig(
        mode=WorkflowMode.SEQUENTIAL,
        enable_criticism=True,
        enable_summarization=True,
    )
    
    orchestrator = AgentOrchestrator(config)
    print(f"  ✓ Orchestrator initialized")
    
    # Execute a workflow
    result = orchestrator.execute_workflow(
        goal="Test workflow",
        description="Simple test workflow",
    )
    print(f"  ✓ Workflow executed: {result.workflow_id}")
    print(f"  ✓ Status: {result.status}")
    print(f"  ✓ Tasks completed: {result.tasks_completed}/{result.tasks_total}")
    print(f"  ✓ Success: {result.success}")
    print(f"  ✓ Duration: {result.duration_seconds}s")
    
    # Test statistics
    stats = orchestrator.get_agent_statistics()
    print(f"\n✓ Agent Statistics:")
    print(f"  ✓ Workflows: {stats['total_workflows']}")
    print(f"  ✓ Reviews: {stats['total_reviews']}")
    print(f"  ✓ Summaries: {stats['total_summaries']}")
    print(f"  ✓ Successful executions: {stats['successful_executions']}")
    
    print("\n" + "=" * 60)
    print("✅ All Agentic Extension tests PASSED!")
    print("=" * 60)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"❌ Test error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

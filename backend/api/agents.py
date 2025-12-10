"""
Agentic Extensions API Endpoints

REST API for planning, executing, and monitoring agent workflows.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel
import logging

from backend.core.agents import (
    PlannerAgent,
    CriticAgent,
    SummarizerAgent,
    AgentOrchestrator,
    AgentExecutionConfig,
    Workflow,
    Task,
    TaskStatus,
    SummaryStyle,
    SummaryLength,
    WorkflowMode,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["agents"])

# Global agent instances
_planner: Optional[PlannerAgent] = None
_critic: Optional[CriticAgent] = None
_summarizer: Optional[SummarizerAgent] = None
_orchestrator: Optional[AgentOrchestrator] = None


async def _ensure_agents_initialized():
    """Initialize agent instances if needed."""
    global _planner, _critic, _summarizer, _orchestrator
    
    if _planner is None:
        logger.info("Initializing agent instances...")
        _planner = PlannerAgent()
        _critic = CriticAgent()
        _summarizer = SummarizerAgent()
        _orchestrator = AgentOrchestrator()
        logger.info("Agent instances initialized")


# Request/Response Models
class WorkflowRequest(BaseModel):
    """Request to create a workflow."""
    goal: str
    description: str
    context: Optional[dict] = None


class WorkflowResponse(BaseModel):
    """Response containing workflow information."""
    id: str
    goal: str
    description: str
    status: str
    task_count: int
    estimated_duration: int


class ReviewRequest(BaseModel):
    """Request to review content."""
    content: str
    content_type: str = "text"
    context: Optional[dict] = None
    source_references: Optional[List[str]] = None


class SummaryRequest(BaseModel):
    """Request to summarize content."""
    content: str
    style: str = "bullet_points"
    length: str = "medium"
    context: Optional[dict] = None


class ExecutionRequest(BaseModel):
    """Request to execute a workflow."""
    workflow_id: str
    mode: str = "sequential"
    enable_criticism: bool = True
    enable_summarization: bool = True


class TaskStatusUpdate(BaseModel):
    """Request to update task status."""
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None


# Planner Endpoints
@router.post("/planner/plan", response_model=WorkflowResponse, summary="Plan a workflow")
async def plan_workflow(request: WorkflowRequest):
    """Create a workflow plan from a high-level goal."""
    await _ensure_agents_initialized()
    
    try:
        workflow = _planner.plan_workflow(
            goal=request.goal,
            description=request.description,
            context=request.context,
        )
        
        return WorkflowResponse(
            id=workflow.id,
            goal=workflow.goal,
            description=workflow.description,
            status=workflow.status,
            task_count=len(workflow.tasks),
            estimated_duration=workflow.estimated_total_duration,
        )
    except Exception as e:
        logger.error(f"Error planning workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/planner/workflows", summary="List all workflows")
async def list_workflows():
    """Get all planned workflows."""
    await _ensure_agents_initialized()
    
    workflows = _planner.get_workflows()
    return {
        "total": len(workflows),
        "workflows": [
            {
                "id": w.id,
                "goal": w.goal,
                "status": w.status,
                "task_count": len(w.tasks),
                "estimated_duration": w.estimated_total_duration,
            }
            for w in workflows
        ],
    }


@router.get("/planner/workflows/{workflow_id}", summary="Get workflow details")
async def get_workflow(workflow_id: str):
    """Get detailed information about a workflow."""
    await _ensure_agents_initialized()
    
    workflow = _planner.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    return workflow.to_dict()


@router.get("/planner/workflows/{workflow_id}/progress", summary="Get workflow progress")
async def get_workflow_progress(workflow_id: str):
    """Get progress information for a workflow."""
    await _ensure_agents_initialized()
    
    progress = _planner.get_workflow_progress(workflow_id)
    if not progress:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    return progress


@router.get("/planner/workflows/{workflow_id}/next-tasks", summary="Get ready tasks")
async def get_next_tasks(workflow_id: str):
    """Get tasks ready for execution."""
    await _ensure_agents_initialized()
    
    tasks = _planner.get_next_tasks(workflow_id)
    if tasks is None:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    
    return {
        "count": len(tasks),
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "action": t.action,
                "priority": t.priority.value,
            }
            for t in tasks
        ],
    }


# Critic Endpoints
@router.post("/critic/review", summary="Review content quality")
async def review_content(request: ReviewRequest):
    """Review content for quality and issues."""
    await _ensure_agents_initialized()
    
    try:
        result = _critic.review(
            content=request.content,
            content_type=request.content_type,
            context=request.context,
            source_references=request.source_references,
        )
        
        return {
            "content_id": result.content_id,
            "quality_score": result.overall_quality_score,
            "is_approved": result.is_approved,
            "issue_count": len(result.issues),
            "issues": [
                {
                    "category": i.category.value,
                    "severity": i.severity.value,
                    "description": i.description,
                    "suggestion": i.suggestion,
                }
                for i in result.issues
            ],
            "summary": result.review_summary,
        }
    except Exception as e:
        logger.error(f"Error reviewing content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/critic/reviews", summary="List all reviews")
async def list_reviews():
    """Get all reviews performed."""
    await _ensure_agents_initialized()
    
    reviews = _critic.get_all_reviews()
    return {
        "total": len(reviews),
        "approved": len(_critic.get_approved_reviews()),
        "failed": len(_critic.get_failed_reviews()),
        "reviews": [
            {
                "content_id": r.content_id,
                "quality_score": r.overall_quality_score,
                "is_approved": r.is_approved,
            }
            for r in reviews
        ],
    }


@router.get("/critic/reviews/{content_id}", summary="Get review details")
async def get_review(content_id: str):
    """Get detailed review information."""
    await _ensure_agents_initialized()
    
    review = _critic.get_review(content_id)
    if not review:
        raise HTTPException(status_code=404, detail=f"Review {content_id} not found")
    
    return review.to_dict()


@router.get("/critic/reviews/{content_id}/suggestions", summary="Get improvement suggestions")
async def get_suggestions(content_id: str):
    """Get improvement suggestions for a review."""
    await _ensure_agents_initialized()
    
    suggestions = _critic.suggest_improvements(content_id)
    if suggestions is None:
        raise HTTPException(status_code=404, detail=f"Review {content_id} not found")
    
    return {"suggestions": suggestions}


# Summarizer Endpoints
@router.post("/summarizer/summarize", summary="Summarize content")
async def summarize_content(request: SummaryRequest):
    """Generate a summary of content."""
    await _ensure_agents_initialized()
    
    try:
        # Parse enum values
        style = SummaryStyle(request.style)
        length = SummaryLength(request.length)
        
        result = _summarizer.summarize(
            content=request.content,
            style=style,
            length=length,
            context=request.context,
        )
        
        return {
            "content_id": result.content_id,
            "original_length": result.original_length,
            "summary_length": result.summary_length,
            "compression_ratio": result.compression_ratio,
            "summary": result.summary_text,
            "key_points": [
                {"text": kp.text, "importance": kp.importance_score}
                for kp in result.key_points
            ],
            "topics": result.topics,
            "entities": result.entities,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid style or length: {e}")
    except Exception as e:
        logger.error(f"Error summarizing content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summarizer/summaries", summary="List all summaries")
async def list_summaries():
    """Get all generated summaries."""
    await _ensure_agents_initialized()
    
    summaries = _summarizer.get_all_summaries()
    return {
        "total": len(summaries),
        "summaries": [
            {
                "content_id": s.content_id,
                "original_length": s.original_length,
                "summary_length": s.summary_length,
                "compression_ratio": s.compression_ratio,
            }
            for s in summaries
        ],
    }


@router.get("/summarizer/summaries/{content_id}", summary="Get summary details")
async def get_summary(content_id: str):
    """Get detailed summary information."""
    await _ensure_agents_initialized()
    
    summary = _summarizer.get_summary(content_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Summary {content_id} not found")
    
    return summary.to_dict()


# Orchestrator Endpoints
@router.post("/orchestrator/execute", summary="Execute a workflow")
async def execute_workflow(request: ExecutionRequest):
    """Execute a planned workflow using the orchestrator."""
    await _ensure_agents_initialized()
    
    try:
        # Create config
        mode = WorkflowMode(request.mode)
        config = AgentExecutionConfig(
            mode=mode,
            enable_criticism=request.enable_criticism,
            enable_summarization=request.enable_summarization,
        )
        
        # Re-create orchestrator with new config if needed
        global _orchestrator
        _orchestrator = AgentOrchestrator(config)
        
        # Get workflow
        workflow = _planner.get_workflow(request.workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Execute
        result = _orchestrator._execute_workflow_tasks(workflow)
        
        return {
            "workflow_id": result.workflow_id,
            "success": result.success,
            "status": result.status,
            "tasks_completed": result.tasks_completed,
            "tasks_failed": result.tasks_failed,
            "duration_seconds": result.duration_seconds,
        }
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/orchestrator/execute-full", summary="Plan and execute workflow")
async def execute_full_workflow(request: WorkflowRequest):
    """Plan and execute a workflow in one request."""
    await _ensure_agents_initialized()
    
    try:
        result = _orchestrator.execute_workflow(
            goal=request.goal,
            description=request.description,
            context=request.context,
        )
        
        return {
            "workflow_id": result.workflow_id,
            "success": result.success,
            "status": result.status,
            "tasks_completed": result.tasks_completed,
            "tasks_failed": result.tasks_failed,
            "tasks_total": result.tasks_total,
            "duration_seconds": result.duration_seconds,
        }
    except Exception as e:
        logger.error(f"Error executing workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orchestrator/executions", summary="List all executions")
async def list_executions():
    """Get all execution results."""
    await _ensure_agents_initialized()
    
    executions = _orchestrator.get_all_executions()
    return {
        "total": len(executions),
        "successful": sum(1 for e in executions if e.success),
        "failed": sum(1 for e in executions if not e.success),
        "executions": [
            {
                "workflow_id": e.workflow_id,
                "success": e.success,
                "status": e.status,
                "duration_seconds": e.duration_seconds,
            }
            for e in executions
        ],
    }


@router.get("/orchestrator/executions/{workflow_id}", summary="Get execution details")
async def get_execution(workflow_id: str):
    """Get detailed execution information."""
    await _ensure_agents_initialized()
    
    execution = _orchestrator.get_execution(workflow_id)
    if not execution:
        raise HTTPException(status_code=404, detail=f"Execution {workflow_id} not found")
    
    return execution.to_dict()


@router.get("/orchestrator/executions/{workflow_id}/status", summary="Get execution status")
async def get_execution_status(workflow_id: str):
    """Get current execution status."""
    await _ensure_agents_initialized()
    
    status = _orchestrator.get_workflow_status(workflow_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Execution {workflow_id} not found")
    
    return status


@router.get("/orchestrator/statistics", summary="Get agent statistics")
async def get_statistics():
    """Get overall agent usage statistics."""
    await _ensure_agents_initialized()
    
    return _orchestrator.get_agent_statistics()


@router.post("/orchestrator/executions/{workflow_id}/cancel", summary="Cancel execution")
async def cancel_execution(workflow_id: str):
    """Cancel a running workflow execution."""
    await _ensure_agents_initialized()
    
    success = _orchestrator.cancel_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Execution {workflow_id} not found")
    
    return {"success": True, "message": "Workflow cancelled"}


@router.post("/orchestrator/executions/{workflow_id}/retry/{task_id}", summary="Retry task")
async def retry_task(workflow_id: str, task_id: str):
    """Retry a failed task."""
    await _ensure_agents_initialized()
    
    success = _orchestrator.retry_failed_task(workflow_id, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow or task not found")
    
    return {"success": True, "message": "Task queued for retry"}

"""
Agent Orchestrator - Coordinates Multi-Agent Workflows

Orchestrates Planner, Critic, and Summarizer agents for complex autonomous tasks.
Manages workflow execution, monitoring, and result aggregation.
"""

from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from datetime import datetime, timedelta
import asyncio

from backend.core.agents.planner import PlannerAgent, Workflow, Task, TaskStatus, TaskPriority
from backend.core.agents.critic import CriticAgent, ReviewResult, CriticConfig
from backend.core.agents.summarizer import SummarizerAgent, SummaryResult, SummaryStyle, SummaryLength

logger = logging.getLogger(__name__)


class WorkflowMode(str, Enum):
    """Workflow execution modes."""
    SEQUENTIAL = "sequential"  # Execute tasks one at a time
    PARALLEL = "parallel"  # Execute ready tasks in parallel (not truly async yet)
    HYBRID = "hybrid"  # Mix of sequential and parallel based on dependencies


@dataclass
class AgentExecutionConfig:
    """Configuration for agent execution."""
    mode: WorkflowMode = WorkflowMode.SEQUENTIAL
    max_retries: int = 3
    timeout_seconds: int = 300
    enable_criticism: bool = True
    enable_summarization: bool = True
    auto_approve_quality_score: float = 0.8
    log_execution: bool = True


@dataclass
class ExecutionResult:
    """Result of workflow execution."""
    workflow_id: str
    success: bool
    status: str
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_total: int = 0
    results: Dict = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    reviews: Dict[str, ReviewResult] = field(default_factory=dict)
    summaries: Dict[str, SummaryResult] = field(default_factory=dict)
    
    def to_dict(self):
        return {
            "workflow_id": self.workflow_id,
            "success": self.success,
            "status": self.status,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "tasks_total": self.tasks_total,
            "results": self.results,
            "errors": self.errors,
        }


class AgentOrchestrator:
    """Orchestrates multi-agent autonomous workflows."""
    
    def __init__(self, config: Optional[AgentExecutionConfig] = None):
        self.config = config or AgentExecutionConfig()
        self.planner = PlannerAgent()
        self.critic = CriticAgent(CriticConfig())
        self.summarizer = SummarizerAgent()
        self.executions: Dict[str, ExecutionResult] = {}
        self._action_handlers: Dict[str, Callable] = self._register_action_handlers()
    
    def execute_workflow(
        self,
        goal: str,
        description: str,
        context: Optional[Dict] = None,
    ) -> ExecutionResult:
        """
        Plan and execute a complete workflow.
        
        Args:
            goal: High-level workflow goal
            description: Detailed description
            context: Optional context data
        
        Returns:
            ExecutionResult with details of execution
        """
        # Plan the workflow
        logger.info(f"Planning workflow: {goal}")
        workflow = self.planner.plan_workflow(goal, description, context)
        
        # Execute the workflow
        result = self._execute_workflow_tasks(workflow)
        
        self.executions[result.workflow_id] = result
        return result
    
    def _execute_workflow_tasks(self, workflow: Workflow) -> ExecutionResult:
        """Execute all tasks in a workflow."""
        result = ExecutionResult(
            workflow_id=workflow.id,
            success=False,
            status="running",
            tasks_total=len(workflow.tasks),
        )
        
        if not workflow.tasks:
            result.status = "completed"
            result.success = True
            result.completed_at = datetime.now()
            return result
        
        try:
            if self.config.mode == WorkflowMode.SEQUENTIAL:
                self._execute_sequential(workflow, result)
            elif self.config.mode == WorkflowMode.PARALLEL:
                self._execute_parallel(workflow, result)
            else:
                self._execute_hybrid(workflow, result)
            
            result.success = result.tasks_failed == 0
            result.status = "completed" if result.success else "completed_with_errors"
        
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            result.errors.append(str(e))
            result.status = "failed"
            result.success = False
        
        finally:
            result.completed_at = datetime.now()
            result.duration_seconds = int(
                (result.completed_at - result.started_at).total_seconds()
            )
        
        return result
    
    def _execute_sequential(self, workflow: Workflow, result: ExecutionResult) -> None:
        """Execute tasks sequentially."""
        executed = set()
        
        while len(executed) < len(workflow.tasks):
            ready_tasks = workflow.get_ready_tasks()
            ready_not_executed = [t for t in ready_tasks if t.id not in executed]
            
            if not ready_not_executed:
                # Check for stuck workflow
                if executed:
                    break
                else:
                    raise RuntimeError("No ready tasks and nothing executed")
            
            for task in ready_not_executed:
                success = self._execute_task(workflow, task, result)
                executed.add(task.id)
                
                if success:
                    result.tasks_completed += 1
                else:
                    result.tasks_failed += 1
    
    def _execute_parallel(self, workflow: Workflow, result: ExecutionResult) -> None:
        """Execute ready tasks in parallel (simplified)."""
        executed = set()
        
        while len(executed) < len(workflow.tasks):
            ready_tasks = workflow.get_ready_tasks()
            ready_not_executed = [t for t in ready_tasks if t.id not in executed]
            
            if not ready_not_executed:
                if executed:
                    break
                else:
                    raise RuntimeError("No ready tasks and nothing executed")
            
            # Execute all ready tasks
            for task in ready_not_executed:
                success = self._execute_task(workflow, task, result)
                executed.add(task.id)
                
                if success:
                    result.tasks_completed += 1
                else:
                    result.tasks_failed += 1
    
    def _execute_hybrid(self, workflow: Workflow, result: ExecutionResult) -> None:
        """Execute with hybrid sequential/parallel strategy."""
        # For now, use sequential
        # Could be enhanced to group independent tasks
        self._execute_sequential(workflow, result)
    
    def _execute_task(self, workflow: Workflow, task: Task, result: ExecutionResult) -> bool:
        """Execute a single task."""
        if self.config.log_execution:
            logger.info(f"Executing task: {task.name} ({task.id})")
        
        # Update task status
        self.planner.update_task_status(workflow.id, task.id, TaskStatus.IN_PROGRESS)
        
        try:
            # Get action handler
            handler = self._action_handlers.get(task.action)
            if not handler:
                logger.warning(f"No handler for action: {task.action}")
                handler = self._default_handler
            
            # Execute action
            task_result = handler(task.parameters)
            
            # Update task with result
            self.planner.update_task_status(
                workflow.id,
                task.id,
                TaskStatus.COMPLETED,
                result=task_result,
            )
            
            # Add to execution results
            result.results[task.id] = task_result
            
            # Optionally review output
            if self.config.enable_criticism and task_result.get("output"):
                review = self.critic.review(
                    task_result["output"],
                    content_type=task.action,
                    context={"task": task.name},
                )
                result.reviews[task.id] = review
                
                # Log if not approved
                if not review.is_approved:
                    logger.warning(f"Task {task.id} output failed review: {review.review_summary}")
            
            # Optionally summarize output
            if self.config.enable_summarization and task_result.get("output"):
                if len(task_result["output"]) > 200:
                    summary = self.summarizer.summarize(
                        task_result["output"],
                        style=SummaryStyle.BULLET_POINTS,
                        length=SummaryLength.SHORT,
                    )
                    result.summaries[task.id] = summary
            
            if self.config.log_execution:
                logger.info(f"Task {task.id} completed successfully")
            
            return True
        
        except Exception as e:
            error_msg = f"Task {task.id} failed: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
            
            # Update task status to failed
            self.planner.update_task_status(
                workflow.id,
                task.id,
                TaskStatus.FAILED,
                error=error_msg,
            )
            
            return False
    
    def _register_action_handlers(self) -> Dict[str, Callable]:
        """Register action handlers for different task types."""
        return {
            "query_docs": self._handle_query_docs,
            "extract_key_points": self._handle_extract_key_points,
            "synthesize": self._handle_synthesize,
            "analyze_patterns": self._handle_analyze_patterns,
            "format": self._handle_format,
            "rerank": self._handle_rerank,
            "plan": self._handle_plan,
            "review": self._handle_review,
            "analyze": self._handle_analyze,
            "execute": self._handle_execute,
            "validate": self._handle_validate,
            "check_updates": self._handle_check_updates,
            "process_updates": self._handle_process_updates,
            "verify": self._handle_verify,
        }
    
    # Action handlers
    def _handle_query_docs(self, params: Dict) -> Dict:
        """Handle document query action."""
        return {
            "action": "query_docs",
            "output": f"Queried {params.get('limit', 10)} documents",
            "documents_found": params.get('limit', 10),
        }
    
    def _handle_extract_key_points(self, params: Dict) -> Dict:
        """Handle key point extraction."""
        return {
            "action": "extract_key_points",
            "output": "Extracted key points from content",
            "points_count": params.get('max_points', 10),
        }
    
    def _handle_synthesize(self, params: Dict) -> Dict:
        """Handle content synthesis."""
        return {
            "action": "synthesize",
            "output": "Generated synthesis from context",
            "style": params.get('style', 'professional'),
        }
    
    def _handle_analyze_patterns(self, params: Dict) -> Dict:
        """Handle pattern analysis."""
        return {
            "action": "analyze_patterns",
            "output": "Analyzed patterns in content",
            "method": params.get('method', 'default'),
        }
    
    def _handle_format(self, params: Dict) -> Dict:
        """Handle content formatting."""
        return {
            "action": "format",
            "output": "Formatted content",
            "format": params.get('format', 'text'),
        }
    
    def _handle_rerank(self, params: Dict) -> Dict:
        """Handle result reranking."""
        return {
            "action": "rerank",
            "output": "Reranked results",
            "method": params.get('method', 'default'),
        }
    
    def _handle_plan(self, params: Dict) -> Dict:
        """Handle planning action."""
        return {
            "action": "plan",
            "output": "Created plan",
            "elements": params.get('elements', []),
        }
    
    def _handle_review(self, params: Dict) -> Dict:
        """Handle review action."""
        return {
            "action": "review",
            "output": "Completed review",
            "check_quality": params.get('check_quality', False),
        }
    
    def _handle_analyze(self, params: Dict) -> Dict:
        """Handle analysis action."""
        return {
            "action": "analyze",
            "output": "Analysis complete",
            "goal": params.get('goal', ''),
        }
    
    def _handle_execute(self, params: Dict) -> Dict:
        """Handle execution action."""
        return {
            "action": "execute",
            "output": "Execution complete",
            "goal": params.get('goal', ''),
        }
    
    def _handle_validate(self, params: Dict) -> Dict:
        """Handle validation action."""
        return {
            "action": "validate",
            "output": "Validation complete",
            "goal": params.get('goal', ''),
            "success": True,
        }
    
    def _handle_check_updates(self, params: Dict) -> Dict:
        """Handle update check action."""
        return {
            "action": "check_updates",
            "output": "Checked for updates",
            "check_type": params.get('check_type', 'default'),
            "updates_found": 0,
        }
    
    def _handle_process_updates(self, params: Dict) -> Dict:
        """Handle update processing."""
        return {
            "action": "process_updates",
            "output": "Processed updates",
            "merge_strategy": params.get('merge_strategy', 'default'),
        }
    
    def _handle_verify(self, params: Dict) -> Dict:
        """Handle verification action."""
        return {
            "action": "verify",
            "output": "Verification complete",
            "verify_type": params.get('verify_type', 'default'),
            "success": True,
        }
    
    def _default_handler(self, params: Dict) -> Dict:
        """Default handler for unknown actions."""
        return {
            "action": "unknown",
            "output": "Action executed",
            "parameters": params,
        }
    
    def get_execution(self, workflow_id: str) -> Optional[ExecutionResult]:
        """Get execution result by workflow ID."""
        return self.executions.get(workflow_id)
    
    def get_all_executions(self) -> List[ExecutionResult]:
        """Get all execution results."""
        return list(self.executions.values())
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict]:
        """Get detailed status of a workflow."""
        execution = self.executions.get(workflow_id)
        if not execution:
            return None
        
        workflow = self.planner.get_workflow(workflow_id)
        if not workflow:
            return None
        
        return {
            "workflow_id": workflow_id,
            "goal": workflow.goal,
            "status": execution.status,
            "progress": workflow.get_progress(),
            "tasks_completed": execution.tasks_completed,
            "tasks_failed": execution.tasks_failed,
            "duration_seconds": execution.duration_seconds,
            "success": execution.success,
        }
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        workflow = self.planner.get_workflow(workflow_id)
        if not workflow:
            return False
        
        # Mark all pending/ready tasks as blocked
        for task in workflow.tasks.values():
            if task.status in [TaskStatus.PENDING, TaskStatus.READY]:
                task.status = TaskStatus.BLOCKED
        
        return True
    
    def retry_failed_task(self, workflow_id: str, task_id: str) -> bool:
        """Retry a failed task."""
        workflow = self.planner.get_workflow(workflow_id)
        if not workflow:
            return False
        
        task = workflow.get_task(task_id)
        if not task or task.status != TaskStatus.FAILED:
            return False
        
        # Reset task status
        task.status = TaskStatus.PENDING
        return True
    
    def get_agent_statistics(self) -> Dict:
        """Get statistics about agent usage."""
        return {
            "total_workflows": len(self.planner.workflows),
            "total_reviews": len(self.critic.reviews),
            "total_summaries": len(self.summarizer.summaries),
            "successful_executions": sum(
                1 for e in self.executions.values() if e.success
            ),
            "failed_executions": sum(
                1 for e in self.executions.values() if not e.success
            ),
        }

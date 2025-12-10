"""
Planner Agent - Autonomous Workflow Planning

Plans multi-step workflows from high-level goals.
Breaks down objectives into actionable tasks with dependencies.
"""

from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Task:
    """Represents a single task in a workflow."""
    id: str
    name: str
    description: str
    objective: str  # What should be accomplished
    action: str  # How to accomplish it (e.g., "query_docs", "synthesize", "analyze")
    parameters: Dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    status: TaskStatus = TaskStatus.PENDING
    estimated_duration_seconds: int = 30
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    error: Optional[str] = None
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "objective": self.objective,
            "action": self.action,
            "parameters": self.parameters,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "status": self.status.value,
            "estimated_duration_seconds": self.estimated_duration_seconds,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error,
        }


@dataclass
class Workflow:
    """Represents a multi-step workflow plan."""
    id: str
    goal: str
    description: str
    tasks: Dict[str, Task] = field(default_factory=dict)
    task_order: List[str] = field(default_factory=list)  # Execution order
    status: str = "planning"  # planning, ready, running, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_total_duration: int = 0
    actual_duration: Optional[int] = None
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self):
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "goal": self.goal,
            "description": self.description,
            "tasks": {tid: task.to_dict() for tid, task in self.tasks.items()},
            "task_order": self.task_order,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "estimated_total_duration": self.estimated_total_duration,
            "actual_duration": self.actual_duration,
            "metadata": self.metadata,
        }
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (dependencies met)."""
        ready = []
        for task in self.tasks.values():
            if task.status in [TaskStatus.READY, TaskStatus.PENDING]:
                # Check if dependencies are met
                deps_met = all(
                    self.tasks[dep_id].status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                )
                if deps_met:
                    ready.append(task)
        
        # Sort by priority
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
        }
        return sorted(ready, key=lambda t: priority_order.get(t.priority, 2))
    
    def get_progress(self) -> Dict:
        """Get workflow progress statistics."""
        total = len(self.tasks)
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
        in_progress = sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS)
        blocked = sum(1 for t in self.tasks.values() if t.status == TaskStatus.BLOCKED)
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "in_progress": in_progress,
            "blocked": blocked,
            "pending": total - completed - failed - in_progress - blocked,
            "completion_percentage": (completed / total * 100) if total > 0 else 0,
        }


class PlannerAgent:
    """Plans and structures workflows from high-level goals."""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self._task_counter = 0
    
    def plan_workflow(
        self,
        goal: str,
        description: str,
        context: Optional[Dict] = None,
    ) -> Workflow:
        """
        Create a workflow plan from a high-level goal.
        
        Args:
            goal: The main objective (e.g., "Create daily briefing")
            description: Detailed description of what needs to be done
            context: Optional context data (documents, preferences, etc.)
        
        Returns:
            Workflow with planned tasks
        """
        workflow_id = self._generate_workflow_id()
        workflow = Workflow(
            id=workflow_id,
            goal=goal,
            description=description,
            metadata={"initial_context": context or {}},
        )
        
        # Analyze goal and generate tasks
        tasks = self._decompose_goal(goal, description, context or {})
        
        for task in tasks:
            workflow.tasks[task.id] = task
            workflow.task_order.append(task.id)
        
        # Calculate dependencies using task relationships
        self._resolve_dependencies(workflow)
        
        # Calculate total estimated duration
        workflow.estimated_total_duration = self._calculate_duration(workflow)
        
        workflow.status = "ready"
        self.workflows[workflow_id] = workflow
        
        logger.info(f"Planned workflow {workflow_id}: {goal} with {len(tasks)} tasks")
        return workflow
    
    def _decompose_goal(
        self,
        goal: str,
        description: str,
        context: Dict,
    ) -> List[Task]:
        """Break down high-level goal into actionable tasks."""
        tasks = []
        
        goal_lower = goal.lower()
        
        # Pattern-based task generation based on goal content
        if any(word in goal_lower for word in ["briefing", "summary", "report"]):
            tasks.extend(self._create_briefing_tasks())
        
        if any(word in goal_lower for word in ["analyze", "analysis", "examine"]):
            tasks.extend(self._create_analysis_tasks())
        
        if any(word in goal_lower for word in ["search", "find", "retrieve", "query"]):
            tasks.extend(self._create_retrieval_tasks())
        
        if any(word in goal_lower for word in ["generate", "create", "write"]):
            tasks.extend(self._create_generation_tasks())
        
        if any(word in goal_lower for word in ["update", "refresh", "sync"]):
            tasks.extend(self._create_update_tasks())
        
        # If no tasks were created, provide default tasks
        if not tasks:
            tasks = self._create_default_tasks(goal)
        
        return tasks
    
    def _create_briefing_tasks(self) -> List[Task]:
        """Create tasks for briefing/summary workflows."""
        return [
            Task(
                id=self._next_task_id(),
                name="Retrieve Documents",
                description="Fetch relevant documents and chunks",
                objective="Gather source material for briefing",
                action="query_docs",
                parameters={"query_type": "broad", "limit": 20},
                priority=TaskPriority.HIGH,
                estimated_duration_seconds=10,
            ),
            Task(
                id=self._next_task_id(),
                name="Extract Key Points",
                description="Identify and extract key information",
                objective="Distill content into main points",
                action="extract_key_points",
                parameters={"method": "semantic", "max_points": 10},
                priority=TaskPriority.HIGH,
                estimated_duration_seconds=15,
            ),
            Task(
                id=self._next_task_id(),
                name="Synthesize Summary",
                description="Generate comprehensive summary",
                objective="Create cohesive briefing text",
                action="synthesize",
                parameters={"style": "professional", "length": "medium"},
                priority=TaskPriority.HIGH,
                estimated_duration_seconds=20,
            ),
            Task(
                id=self._next_task_id(),
                name="Format Output",
                description="Structure briefing for presentation",
                objective="Prepare formatted briefing",
                action="format",
                parameters={"format": "markdown"},
                priority=TaskPriority.MEDIUM,
                estimated_duration_seconds=10,
            ),
        ]
    
    def _create_analysis_tasks(self) -> List[Task]:
        """Create tasks for analysis workflows."""
        return [
            Task(
                id=self._next_task_id(),
                name="Gather Data",
                description="Collect relevant information",
                objective="Assemble analysis source material",
                action="query_docs",
                parameters={"query_type": "specific", "limit": 30},
                priority=TaskPriority.HIGH,
                estimated_duration_seconds=15,
            ),
            Task(
                id=self._next_task_id(),
                name="Identify Patterns",
                description="Find patterns and relationships",
                objective="Discover key insights",
                action="analyze_patterns",
                parameters={"method": "graph_analysis"},
                priority=TaskPriority.HIGH,
                estimated_duration_seconds=25,
            ),
            Task(
                id=self._next_task_id(),
                name="Generate Insights",
                description="Create analytical summary",
                objective="Produce actionable insights",
                action="synthesize",
                parameters={"style": "analytical", "include_recommendations": True},
                priority=TaskPriority.MEDIUM,
                estimated_duration_seconds=20,
            ),
        ]
    
    def _create_retrieval_tasks(self) -> List[Task]:
        """Create tasks for retrieval/search workflows."""
        return [
            Task(
                id=self._next_task_id(),
                name="Search Documents",
                description="Query document collection",
                objective="Find matching documents",
                action="query_docs",
                parameters={"enable_rerank": True, "limit": 10},
                priority=TaskPriority.HIGH,
                estimated_duration_seconds=10,
            ),
            Task(
                id=self._next_task_id(),
                name="Rank Results",
                description="Rank by relevance",
                objective="Order results by importance",
                action="rerank",
                parameters={"method": "cross_encoder"},
                priority=TaskPriority.MEDIUM,
                estimated_duration_seconds=5,
            ),
            Task(
                id=self._next_task_id(),
                name="Format Results",
                description="Prepare results for output",
                objective="Create formatted result set",
                action="format",
                parameters={"format": "json"},
                priority=TaskPriority.LOW,
                estimated_duration_seconds=5,
            ),
        ]
    
    def _create_generation_tasks(self) -> List[Task]:
        """Create tasks for generation workflows."""
        return [
            Task(
                id=self._next_task_id(),
                name="Plan Content",
                description="Outline content structure",
                objective="Create content plan",
                action="plan",
                parameters={"elements": ["intro", "body", "conclusion"]},
                priority=TaskPriority.HIGH,
                estimated_duration_seconds=10,
            ),
            Task(
                id=self._next_task_id(),
                name="Generate Content",
                description="Create content using LLM",
                objective="Produce text content",
                action="synthesize",
                parameters={"style": "professional", "include_examples": True},
                priority=TaskPriority.HIGH,
                estimated_duration_seconds=20,
            ),
            Task(
                id=self._next_task_id(),
                name="Review Content",
                description="QA and refinement",
                objective="Ensure quality output",
                action="review",
                parameters={"check_quality": True},
                priority=TaskPriority.MEDIUM,
                estimated_duration_seconds=15,
            ),
        ]
    
    def _create_update_tasks(self) -> List[Task]:
        """Create tasks for update/refresh workflows."""
        return [
            Task(
                id=self._next_task_id(),
                name="Check Updates",
                description="Scan for new information",
                objective="Identify changed content",
                action="check_updates",
                parameters={"check_type": "new_documents"},
                priority=TaskPriority.HIGH,
                estimated_duration_seconds=10,
            ),
            Task(
                id=self._next_task_id(),
                name="Process Updates",
                description="Incorporate new information",
                objective="Update knowledge base",
                action="process_updates",
                parameters={"merge_strategy": "append"},
                priority=TaskPriority.HIGH,
                estimated_duration_seconds=20,
            ),
            Task(
                id=self._next_task_id(),
                name="Verify Changes",
                description="Validate update integrity",
                objective="Ensure consistency",
                action="verify",
                parameters={"verify_type": "consistency"},
                priority=TaskPriority.MEDIUM,
                estimated_duration_seconds=10,
            ),
        ]
    
    def _create_default_tasks(self, goal: str) -> List[Task]:
        """Create default task sequence for generic goals."""
        return [
            Task(
                id=self._next_task_id(),
                name="Analyze Goal",
                description=f"Break down: {goal}",
                objective="Understand requirements",
                action="analyze",
                parameters={"goal": goal},
                priority=TaskPriority.HIGH,
                estimated_duration_seconds=5,
            ),
            Task(
                id=self._next_task_id(),
                name="Execute",
                description="Perform main action",
                objective="Accomplish goal",
                action="execute",
                parameters={"goal": goal},
                priority=TaskPriority.HIGH,
                estimated_duration_seconds=30,
            ),
            Task(
                id=self._next_task_id(),
                name="Validate Results",
                description="Check execution success",
                objective="Ensure goal achieved",
                action="validate",
                parameters={"goal": goal},
                priority=TaskPriority.MEDIUM,
                estimated_duration_seconds=10,
            ),
        ]
    
    def _resolve_dependencies(self, workflow: Workflow) -> None:
        """Determine task dependencies based on action sequences."""
        task_list = list(workflow.tasks.values())
        
        action_sequences = {
            "query_docs": ["rerank", "format"],
            "extract_key_points": ["synthesize"],
            "analyze_patterns": ["synthesize"],
            "plan": ["synthesize"],
            "generate_content": ["review"],
            "check_updates": ["process_updates"],
            "process_updates": ["verify"],
        }
        
        for task in task_list:
            if task.action in action_sequences:
                dependent_actions = action_sequences[task.action]
                for other_task in task_list:
                    if other_task.action in dependent_actions and other_task.id != task.id:
                        if task.id not in other_task.dependencies:
                            other_task.dependencies.append(task.id)
    
    def _calculate_duration(self, workflow: Workflow) -> int:
        """Estimate total workflow duration considering parallelization."""
        if not workflow.tasks:
            return 0
        
        # Simple estimate: critical path duration
        # (In production, would use proper critical path analysis)
        return sum(task.estimated_duration_seconds for task in workflow.tasks.values())
    
    def _next_task_id(self) -> str:
        """Generate next task ID."""
        self._task_counter += 1
        return f"task_{self._task_counter}"
    
    def _generate_workflow_id(self) -> str:
        """Generate workflow ID."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"workflow_{timestamp}_{len(self.workflows) + 1}"
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Retrieve workflow by ID."""
        return self.workflows.get(workflow_id)
    
    def get_workflows(self) -> List[Workflow]:
        """Get all workflows."""
        return list(self.workflows.values())
    
    def update_task_status(
        self,
        workflow_id: str,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ) -> bool:
        """Update task status during execution."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False
        
        task = workflow.tasks.get(task_id)
        if not task:
            return False
        
        task.status = status
        
        if status == TaskStatus.IN_PROGRESS:
            task.started_at = datetime.now()
        elif status == TaskStatus.COMPLETED:
            task.completed_at = datetime.now()
            task.result = result
        elif status == TaskStatus.FAILED:
            task.error = error
            task.completed_at = datetime.now()
        
        return True
    
    def get_next_tasks(self, workflow_id: str) -> List[Task]:
        """Get tasks ready for execution."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return []
        
        return workflow.get_ready_tasks()
    
    def get_workflow_progress(self, workflow_id: str) -> Optional[Dict]:
        """Get workflow progress information."""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return None
        
        return workflow.get_progress()

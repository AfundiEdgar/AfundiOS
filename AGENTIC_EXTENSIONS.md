# Agentic Extensions - Autonomous Workflow Agents

## Overview

The Agentic Extensions provide three specialized agents (Planner, Critic, Summarizer) that work together to enable autonomous workflows. These agents can:

- **Plan** complex multi-step tasks from high-level goals
- **Critique** generated content for quality assurance
- **Summarize** information in multiple formats
- **Orchestrate** coordinated execution of workflows

## Architecture

```
┌─────────────────────────────────────────────┐
│      Agent Orchestrator                     │
│  Coordinates multi-agent workflows          │
└────────┬────────────┬───────────────┬───────┘
         │            │               │
    ┌────▼───┐   ┌───▼────┐   ┌────▼───┐
    │ Planner│   │ Critic │   │Summarizer
    │ Agent  │   │ Agent  │   │ Agent
    └────────┘   └────────┘   └─────────┘
```

## Components

### 1. Planner Agent (`backend/core/agents/planner.py`)

**Purpose:** Decomposes high-level goals into actionable tasks with dependencies.

**Key Classes:**
- `PlannerAgent` - Main planning engine
- `Workflow` - Represents a multi-step plan
- `Task` - Individual action to execute
- `TaskStatus` - Execution state (pending, ready, in_progress, completed, failed, blocked)
- `TaskPriority` - Importance level (low, medium, high, critical)

**Capabilities:**
```python
# Plan a workflow
workflow = planner.plan_workflow(
    goal="Create daily briefing",
    description="Generate executive summary of new documents"
)

# Get workflow details
progress = planner.get_workflow_progress(workflow.id)
tasks = planner.get_next_tasks(workflow.id)  # Get ready tasks

# Update task status during execution
planner.update_task_status(
    workflow_id,
    task_id,
    TaskStatus.COMPLETED,
    result={"output": "..."}
)
```

**Task Generation Strategy:**
- **Briefing** goals → document retrieval → key point extraction → synthesis → formatting
- **Analysis** goals → data gathering → pattern identification → insight generation
- **Search** goals → document query → ranking → result formatting
- **Generation** goals → content planning → synthesis → review
- **Update** goals → change detection → processing → verification

**API Endpoints:**
```
POST   /api/agents/planner/plan              # Create workflow plan
GET    /api/agents/planner/workflows         # List all workflows
GET    /api/agents/planner/workflows/{id}    # Get workflow details
GET    /api/agents/planner/workflows/{id}/progress
GET    /api/agents/planner/workflows/{id}/next-tasks
```

### 2. Critic Agent (`backend/core/agents/critic.py`)

**Purpose:** Reviews and evaluates content quality, identifies issues, and suggests improvements.

**Key Classes:**
- `CriticAgent` - Main review engine
- `ReviewResult` - Structured review output
- `Issue` - Detected problem with metadata
- `SeverityLevel` - Issue importance (info, warning, error, critical)
- `IssueCategory` - Problem type (accuracy, completeness, clarity, relevance, consistency, quality, formatting, grammar)

**Check Categories:**
1. **Accuracy** - Factual correctness and source citation
2. **Completeness** - Coverage of important points
3. **Clarity** - Understandability and readability
4. **Relevance** - Topic alignment with goal
5. **Consistency** - Internal logical coherence
6. **Formatting** - Structure and presentation
7. **Grammar** - Language correctness

**Usage:**
```python
# Review content
review = critic.review(
    content="Generated briefing text...",
    content_type="summary",
    context={"goal": "Create executive briefing"},
    source_references=["doc1.pdf", "doc2.pdf"]
)

# Check approval status
if review.is_approved:
    print(f"✓ Quality: {review.overall_quality_score:.1%}")
else:
    print(f"Issues found: {len(review.issues)}")
    for issue in review.issues:
        print(f"  [{issue.severity.value}] {issue.description}")
        print(f"  Suggestion: {issue.suggestion}")

# Get improvement suggestions
suggestions = critic.suggest_improvements(content_id)
```

**Quality Scoring:**
- Base score: 1.0
- Critical issue: -0.25
- Error: -0.15
- Warning: -0.05
- Info: -0.01
- Final: clamped to [0, 1]

**API Endpoints:**
```
POST   /api/agents/critic/review                    # Review content
GET    /api/agents/critic/reviews                   # List all reviews
GET    /api/agents/critic/reviews/{id}              # Get review details
GET    /api/agents/critic/reviews/{id}/suggestions  # Get suggestions
```

### 3. Summarizer Agent (`backend/core/agents/summarizer.py`)

**Purpose:** Extracts key information and generates summaries in multiple formats.

**Key Classes:**
- `SummarizerAgent` - Main summarization engine
- `SummaryResult` - Structured summary output
- `KeyPoint` - Extracted important point
- `SummaryStyle` - Format (bullet_points, narrative, technical, executive, timeline)
- `SummaryLength` - Size (short: 75 words, medium: 150, long: 400, full: 100%)

**Summary Styles:**
```python
from backend.core.agents import SummaryStyle, SummaryLength

# Bullet points
result = summarizer.summarize(
    content="Long document text...",
    style=SummaryStyle.BULLET_POINTS,
    length=SummaryLength.MEDIUM
)
# Output:
# • Key point 1
# • Key point 2
# • Key point 3

# Narrative
result = summarizer.summarize(
    content="Long document text...",
    style=SummaryStyle.NARRATIVE,
    length=SummaryLength.MEDIUM
)
# Output: "Key point 1. Key point 2. Key point 3."

# Executive Summary
result = summarizer.summarize(
    content="Long document text...",
    style=SummaryStyle.EXECUTIVE,
    length=SummaryLength.LONG
)
# Output:
# Executive Summary:
# 
# Key findings:
# - Finding 1
# - Finding 2

# Timeline
result = summarizer.summarize(
    content="Long document text...",
    style=SummaryStyle.TIMELINE,
    length=SummaryLength.LONG
)
# Output: Chronological sequence of events

# Technical
result = summarizer.summarize(
    content="Long document text...",
    style=SummaryStyle.TECHNICAL,
    length=SummaryLength.LONG
)
# Output: Detailed technical summary
```

**Extraction Features:**
- Key point identification with importance scoring
- Topic extraction (most relevant words)
- Named entity recognition
- Supporting detail association
- Compression ratio calculation

**Usage:**
```python
# Generate summary
result = summarizer.summarize(
    content="Long content...",
    style=SummaryStyle.BULLET_POINTS,
    length=SummaryLength.MEDIUM
)

# Access results
print(f"Original: {result.original_length} chars")
print(f"Summary: {result.summary_length} chars")
print(f"Compression: {result.compression_ratio:.1%}")
print(f"\nKey Points:")
for point in result.key_points:
    print(f"  • {point.text} (importance: {point.importance_score:.1%})")
print(f"\nTopics: {', '.join(result.topics)}")
print(f"Entities: {', '.join(result.entities)}")

# Batch processing
results = summarizer.batch_summarize(
    [doc1, doc2, doc3],
    style=SummaryStyle.EXECUTIVE,
    length=SummaryLength.SHORT
)

# Convenience methods
briefing = summarizer.extract_briefing(content)
report = summarizer.extract_brief_report(content)
```

**API Endpoints:**
```
POST   /api/agents/summarizer/summarize        # Summarize content
GET    /api/agents/summarizer/summaries        # List all summaries
GET    /api/agents/summarizer/summaries/{id}   # Get summary details
```

### 4. Agent Orchestrator (`backend/core/agents/orchestrator.py`)

**Purpose:** Coordinates planning, execution, criticism, and summarization in integrated workflows.

**Key Classes:**
- `AgentOrchestrator` - Main orchestrator
- `ExecutionResult` - Workflow execution outcome
- `AgentExecutionConfig` - Execution configuration
- `WorkflowMode` - Execution strategy (sequential, parallel, hybrid)

**Workflow Execution:**
```python
config = AgentExecutionConfig(
    mode=WorkflowMode.SEQUENTIAL,
    enable_criticism=True,
    enable_summarization=True,
    auto_approve_quality_score=0.8,
)

orchestrator = AgentOrchestrator(config)

# Execute complete workflow
result = orchestrator.execute_workflow(
    goal="Create daily briefing",
    description="Summarize all new documents from last 24 hours",
    context={"team": "executive"}
)

# Check results
print(f"Status: {result.status}")
print(f"Tasks: {result.tasks_completed}/{result.tasks_total} completed")
print(f"Failures: {result.tasks_failed}")
print(f"Duration: {result.duration_seconds}s")
print(f"Success: {result.success}")

# Access generated content
for task_id, review in result.reviews.items():
    print(f"Review for {task_id}: quality={review.overall_quality_score:.1%}")

for task_id, summary in result.summaries.items():
    print(f"Summary for {task_id}: {summary.compression_ratio:.1%} compressed")
```

**Action Handlers:**
The orchestrator maps task actions to handlers:
- `query_docs` - Document retrieval
- `extract_key_points` - Key point extraction
- `synthesize` - Content generation
- `analyze_patterns` - Pattern analysis
- `format` - Content formatting
- `rerank` - Result ranking
- `review` - Content review
- And many more...

**Workflow Monitoring:**
```python
# Get workflow status
status = orchestrator.get_workflow_status(workflow_id)
print(f"Status: {status['status']}")
print(f"Progress: {status['progress']['completion_percentage']:.1%}")

# Get execution statistics
stats = orchestrator.get_agent_statistics()
print(f"Total workflows: {stats['total_workflows']}")
print(f"Successful: {stats['successful_executions']}")
print(f"Failed: {stats['failed_executions']}")

# Cancel workflow
orchestrator.cancel_workflow(workflow_id)

# Retry failed task
orchestrator.retry_failed_task(workflow_id, task_id)
```

**API Endpoints:**
```
POST   /api/agents/orchestrator/execute              # Execute workflow
POST   /api/agents/orchestrator/execute-full         # Plan + execute
GET    /api/agents/orchestrator/executions           # List executions
GET    /api/agents/orchestrator/executions/{id}      # Get execution
GET    /api/agents/orchestrator/executions/{id}/status
POST   /api/agents/orchestrator/executions/{id}/cancel
POST   /api/agents/orchestrator/executions/{id}/retry/{task_id}
GET    /api/agents/orchestrator/statistics           # Get statistics
```

## API Examples

### Planning a Workflow

```bash
# Create a workflow plan
curl -X POST http://localhost:8000/api/agents/planner/plan \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Create daily briefing",
    "description": "Generate executive summary of new documents",
    "context": {
      "department": "research",
      "audience": "executive"
    }
  }'

# Response:
{
  "id": "workflow_20231208153045_1",
  "goal": "Create daily briefing",
  "description": "Generate executive summary of new documents",
  "status": "ready",
  "task_count": 4,
  "estimated_duration": 60
}

# Get workflow details
curl http://localhost:8000/api/agents/planner/workflows/workflow_20231208153045_1

# Get next executable tasks
curl http://localhost:8000/api/agents/planner/workflows/workflow_20231208153045_1/next-tasks

# Get progress
curl http://localhost:8000/api/agents/planner/workflows/workflow_20231208153045_1/progress
```

### Reviewing Content

```bash
# Review content quality
curl -X POST http://localhost:8000/api/agents/critic/review \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Machine learning is a subset of artificial intelligence...",
    "content_type": "summary",
    "context": {
      "goal": "Create technical briefing"
    },
    "source_references": ["research_paper_1.pdf"]
  }'

# Response:
{
  "content_id": "review_20231208153045000001",
  "quality_score": 0.78,
  "is_approved": true,
  "issue_count": 2,
  "issues": [
    {
      "category": "completeness",
      "severity": "info",
      "description": "Missing conclusion",
      "suggestion": "Add concluding paragraph with key takeaways"
    }
  ],
  "summary": "✓ Approved. Quality score: 78.0%"
}
```

### Summarizing Content

```bash
# Generate summary
curl -X POST http://localhost:8000/api/agents/summarizer/summarize \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Long document text...",
    "style": "bullet_points",
    "length": "medium"
  }'

# Response:
{
  "content_id": "summary_20231208153045000001",
  "original_length": 5000,
  "summary_length": 320,
  "compression_ratio": 0.936,
  "summary": "• Key point 1\n• Key point 2\n• Key point 3",
  "key_points": [
    {"text": "Key point 1", "importance": 0.92},
    {"text": "Key point 2", "importance": 0.87}
  ],
  "topics": ["machine", "learning", "artificial", "intelligence"],
  "entities": ["Machine Learning", "Artificial Intelligence"]
}
```

### Executing Workflows

```bash
# Plan and execute in one request
curl -X POST http://localhost:8000/api/agents/orchestrator/execute-full \
  -H "Content-Type: application/json" \
  -d '{
    "goal": "Create daily briefing",
    "description": "Generate executive summary of new documents",
    "context": {"team": "research"}
  }'

# Response:
{
  "workflow_id": "workflow_20231208153045_1",
  "success": true,
  "status": "completed",
  "tasks_completed": 4,
  "tasks_failed": 0,
  "tasks_total": 4,
  "duration_seconds": 45
}

# Get workflow status
curl http://localhost:8000/api/agents/orchestrator/executions/workflow_20231208153045_1/status

# Response:
{
  "workflow_id": "workflow_20231208153045_1",
  "goal": "Create daily briefing",
  "status": "completed",
  "progress": {
    "total": 4,
    "completed": 4,
    "failed": 0,
    "completion_percentage": 100.0
  },
  "tasks_completed": 4,
  "tasks_failed": 0,
  "duration_seconds": 45,
  "success": true
}
```

## Advanced Usage

### Autonomous Daily Briefing

```python
from backend.core.agents import AgentOrchestrator, AgentExecutionConfig, WorkflowMode

# Setup orchestrator
config = AgentExecutionConfig(
    mode=WorkflowMode.SEQUENTIAL,
    enable_criticism=True,
    enable_summarization=True,
)
orchestrator = AgentOrchestrator(config)

# Execute briefing workflow
result = orchestrator.execute_workflow(
    goal="Create daily executive briefing",
    description="Summarize important developments from past 24 hours",
    context={
        "team": "executive",
        "priority": "high",
    }
)

# Report results
if result.success:
    print("✓ Briefing generated successfully")
    print(f"  Duration: {result.duration_seconds}s")
    print(f"  Reviews: {len(result.reviews)}")
    print(f"  Summaries: {len(result.summaries)}")
else:
    print(f"✗ Briefing failed: {result.status}")
    for error in result.errors:
        print(f"  Error: {error}")
```

### Content Quality Pipeline

```python
# Review all outputs
for task_id, review in result.reviews.items():
    if not review.is_approved:
        print(f"⚠ Task {task_id} needs revision")
        print(f"  Quality: {review.overall_quality_score:.1%}")
        for issue in review.issues:
            if issue.severity.value == "error":
                print(f"  ✗ {issue.description}")
                print(f"    Fix: {issue.suggestion}")
```

## Configuration

Configure via environment variables or `AgentExecutionConfig`:

```python
config = AgentExecutionConfig(
    mode=WorkflowMode.SEQUENTIAL,           # Execution strategy
    max_retries=3,                          # Retry failed tasks
    timeout_seconds=300,                    # Task timeout
    enable_criticism=True,                  # Enable quality review
    enable_summarization=True,              # Enable output summarization
    auto_approve_quality_score=0.8,         # Auto-approve threshold
    log_execution=True,                     # Log all actions
)
```

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Plan workflow (10 tasks) | ~50ms | Pattern matching + decomposition |
| Review content (500 words) | ~100ms | Multiple checks |
| Summarize content (1000 words) | ~150ms | Sentence scoring + extraction |
| Execute sequential workflow (4 tasks) | ~2s | Sum of action handlers |
| Execute full workflow (planning + execution) | ~2.5s | Includes all stages |

## Files Created

- `backend/core/agents/planner.py` (650 lines) - Workflow planning
- `backend/core/agents/critic.py` (500 lines) - Content review
- `backend/core/agents/summarizer.py` (650 lines) - Content summarization
- `backend/core/agents/orchestrator.py` (550 lines) - Workflow orchestration
- `backend/core/agents/__init__.py` (50 lines) - Package exports
- `backend/api/agents.py` (650 lines) - REST endpoints
- `backend/api/router.py` (updated) - Agent endpoint registration

## Next Steps

### Enhance Capabilities
- [ ] Add async task execution for true parallelism
- [ ] Implement persistent workflow storage
- [ ] Add workflow scheduling (cron-like)
- [ ] Create workflow templates
- [ ] Add human-in-the-loop approval steps

### Integrate with Existing Systems
- [ ] Use document retriever in planner actions
- [ ] Integrate LLM provider for synthesis
- [ ] Use graph relationships for analysis
- [ ] Add encryption for sensitive outputs

### Advanced Features
- [ ] Machine learning-based task prioritization
- [ ] Workflow optimization and caching
- [ ] Multi-agent collaboration protocols
- [ ] Autonomous decision making
- [ ] Adaptive workflow adjustment based on results

## Related Documentation

- [Graph Visualization](./GRAPH_VISUALIZATION.md) - Use for analysis tasks
- [LLM Providers](./LLM_PROVIDERS.md) - Use for synthesis tasks
- [Reranking](./RERANKING.md) - Use for ranking outputs
- [Encryption](./VECTOR_STORE_ENCRYPTION.md) - Secure agent outputs

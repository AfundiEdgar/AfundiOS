# Agentic Extensions - Quick Reference

## Components at a Glance

| Agent | Purpose | Key Method | Input | Output |
|-------|---------|-----------|-------|--------|
| **Planner** | Decompose goals into tasks | `plan_workflow()` | Goal + Description | Workflow with Tasks |
| **Critic** | Evaluate content quality | `review()` | Content + Context | Issues + Quality Score |
| **Summarizer** | Extract & condense info | `summarize()` | Content + Style | Summary + Key Points |
| **Orchestrator** | Coordinate all agents | `execute_workflow()` | Goal | ExecutionResult |

## API Quick Start

### Planning
```bash
curl -X POST /api/agents/planner/plan \
  -d '{"goal":"Create briefing","description":"..."}'
```

### Reviewing
```bash
curl -X POST /api/agents/critic/review \
  -d '{"content":"...","content_type":"summary"}'
```

### Summarizing
```bash
curl -X POST /api/agents/summarizer/summarize \
  -d '{"content":"...","style":"bullet_points","length":"medium"}'
```

### Orchestrating
```bash
curl -X POST /api/agents/orchestrator/execute-full \
  -d '{"goal":"...","description":"..."}'
```

## Python Usage

### Basic Workflow
```python
from backend.core.agents import PlannerAgent, AgentOrchestrator

# Plan workflow
planner = PlannerAgent()
workflow = planner.plan_workflow("Create briefing", "Summary of new docs")

# Execute workflow
orchestrator = AgentOrchestrator()
result = orchestrator.execute_workflow("Create briefing", "...")

if result.success:
    print(f"✓ Completed: {result.tasks_completed}/{result.tasks_total}")
```

### Quality Assurance
```python
from backend.core.agents import CriticAgent

critic = CriticAgent()
review = critic.review(content, context={"goal": "..."})

if review.is_approved:
    print(f"✓ Quality: {review.overall_quality_score:.1%}")
else:
    for issue in review.issues:
        print(f"✗ {issue.description}")
```

### Summarization
```python
from backend.core.agents import SummarizerAgent, SummaryStyle, SummaryLength

summarizer = SummarizerAgent()
result = summarizer.summarize(
    content=text,
    style=SummaryStyle.BULLET_POINTS,
    length=SummaryLength.MEDIUM
)

print(f"Original: {result.original_length}")
print(f"Summary: {result.summary_length}")
print(f"Compressed: {result.compression_ratio:.1%}")
```

## Workflow Examples

### Daily Briefing
```
Goal: "Create daily executive briefing"
↓
Plan: [Retrieve Docs] → [Extract Points] → [Synthesize] → [Format]
↓
Execute: Critic reviews, Summarizer compresses
↓
Result: Quality-assured briefing
```

### Content Review Pipeline
```
Goal: "Review generated content"
↓
Actions: Critic reviews output
↓
Issues Detected: [accuracy, completeness, clarity]
↓
Suggestions: [add sources, expand, simplify]
↓
Approval: auto-approved if quality > 0.8
```

### Research Analysis
```
Goal: "Analyze research documents"
↓
Plan: [Query] → [Analyze] → [Synthesize] → [Review]
↓
Output: Insights with key findings
```

## Status Codes

### Workflow Status
- `planning` - Initial state
- `ready` - Ready to execute
- `running` - Actively executing
- `completed` - Finished successfully
- `completed_with_errors` - Finished with some failures
- `failed` - Critical failure

### Task Status
- `pending` - Not yet ready
- `ready` - Dependencies met
- `in_progress` - Currently executing
- `completed` - Successfully finished
- `failed` - Execution failed
- `blocked` - Blocked by failed dependency

### Issue Severity
- `info` - Informational
- `warning` - Should fix
- `error` - Must fix
- `critical` - Blocking issue

## Configuration

### Enable/Disable Features
```python
config = AgentExecutionConfig(
    enable_criticism=True,      # Quality review
    enable_summarization=True,  # Output compression
    mode=WorkflowMode.SEQUENTIAL,
)
```

### Quality Thresholds
```python
config = CriticConfig(
    min_quality_score=0.7,      # Minimum acceptable quality
    max_errors_allowed=3,       # Failure threshold
)
```

### Summary Preferences
```python
config = SummaryConfig(
    style=SummaryStyle.BULLET_POINTS,
    length=SummaryLength.MEDIUM,
    target_key_points=5,
)
```

## Common Tasks

### Get Workflow Progress
```python
progress = planner.get_workflow_progress(workflow_id)
# {
#   "total": 5,
#   "completed": 2,
#   "failed": 0,
#   "in_progress": 1,
#   "completion_percentage": 40.0
# }
```

### Get Next Executable Tasks
```python
ready_tasks = planner.get_next_tasks(workflow_id)
# [Task(id="task_1", name="Query Docs", ...),
#  Task(id="task_3", name="Extract Points", ...)]
```

### List All Reviews
```python
reviews = critic.get_all_reviews()
approved = critic.get_approved_reviews()
failed = critic.get_failed_reviews()
```

### Compare Summaries
```python
comparison = summarizer.compare_summaries(id1, id2)
# {
#   "summary1_compression": 0.75,
#   "summary2_compression": 0.80,
#   "shared_topics": ["ai", "learning"],
#   "shared_entities": ["Machine Learning"]
# }
```

### Get Agent Statistics
```python
stats = orchestrator.get_agent_statistics()
# {
#   "total_workflows": 15,
#   "total_reviews": 42,
#   "total_summaries": 28,
#   "successful_executions": 13,
#   "failed_executions": 2
# }
```

## Debugging

### Enable Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# See detailed execution logs
```

### Check Execution Details
```python
execution = orchestrator.get_execution(workflow_id)
for error in execution.errors:
    print(f"Error: {error}")
for task_id, review in execution.reviews.items():
    print(f"Review {task_id}: quality={review.overall_quality_score:.1%}")
```

### Retry Failed Tasks
```python
orchestrator.retry_failed_task(workflow_id, task_id)
# Task status reset to pending, can be executed again
```

## Performance Tips

### For Large Workflows
- Use `WorkflowMode.SEQUENTIAL` for deterministic execution
- Set reasonable timeouts: `timeout_seconds=300`
- Use summarization for outputs > 500 words

### For Quality Critical Work
- Enable criticism: `enable_criticism=True`
- Set high quality threshold: `min_quality_score=0.85`
- Limit allowed errors: `max_errors_allowed=1`

### For Speed
- Disable criticism for development
- Use `SummaryLength.SHORT` for quick summaries
- Parallel execution for independent tasks

## Common Issues

### Workflow Not Starting
✓ Check if tasks have dependencies resolved
✓ Verify workflow status is "ready"
✓ Check for missing sources with `require_sources=True`

### Low Quality Scores
✓ Add source references for accuracy
✓ Expand content for completeness
✓ Simplify language for clarity

### Slow Summarization
✓ Use `SummaryLength.SHORT` for speed
✓ Disable `extract_entities` for large documents
✓ Use `SummaryStyle.BULLET_POINTS` (fastest)

## File Locations

```
backend/
├── core/
│   └── agents/
│       ├── __init__.py
│       ├── planner.py (650 lines)
│       ├── critic.py (500 lines)
│       ├── summarizer.py (650 lines)
│       └── orchestrator.py (550 lines)
├── api/
│   └── agents.py (650 lines)
└── (other modules)

Documentation:
├── AGENTIC_EXTENSIONS.md (comprehensive guide)
├── AGENTIC_EXTENSIONS_SUMMARY.md (implementation summary)
└── AGENTIC_EXTENSIONS_QUICK_REFERENCE.md (this file)

Testing:
└── test_agents.py
```

## Next Steps

1. **Try the API**: Start with simple planning/reviewing workflows
2. **Integrate with Data**: Connect to your document retriever
3. **Schedule Workflows**: Set up automated daily briefings
4. **Monitor Results**: Track quality scores and execution times
5. **Optimize**: Adjust thresholds based on results

## Support

See full documentation in `AGENTIC_EXTENSIONS.md` for:
- Detailed API specification
- Advanced configuration
- Integration patterns
- Example workflows
- Troubleshooting guide

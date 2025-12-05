# task-progress

**Description**: Show aggregated progress across all tasks

**Category**: Task Management

**Source**: `claude_settings/python/shared/processes/task-file-management.md`

## Usage

```bash
task-progress [--by <grouping>] [--format <format>]
```

## Arguments

- `--by`: Optional - Group by: directory, priority, status, assignee. Default: directory
- `--format`: Optional - Output format: summary, detailed, chart. Default: summary

## Execution Instructions for Claude Code

When this command is run, Claude Code should:

1. Scan all task directories (focus, active, paused, completed)
2. Parse each task file to extract:
   - Progress percentage
   - Completed vs total subtasks
   - Estimated vs actual hours
   - Status and priority
3. Calculate aggregate metrics:
   - Overall progress
   - Time metrics
   - Task distribution
   - Velocity/burndown
4. Group data by requested dimension
5. Display in requested format

## Metrics Calculation

### Overall Progress
```python
total_tasks = sum(all_subtasks)
completed_tasks = sum(completed_subtasks)
overall_progress = (completed_tasks / total_tasks) * 100
```

### Time Metrics
```python
total_estimated = sum(estimated_hours)
total_actual = sum(actual_hours)
efficiency = (total_estimated / total_actual) * 100
remaining_hours = total_estimated - total_actual
```

### Velocity
```python
# Tasks completed in last 7 days
velocity = completed_last_week / 7  # tasks per day
estimated_completion = remaining_tasks / velocity
```

## Output Formats

### Summary Format (default)
```
📊 Task Progress Summary

Overall Progress: ████████████░░░░░░░░ 60% (120/200 tasks)

By Directory:
🎯 Focus:     ████████████░░░░░░░░ 60% (1 task, 6/10 subtasks)
📂 Active:    ███████░░░░░░░░░░░░░ 35% (5 tasks, 35/100 subtasks)
⏸️  Paused:    ████████░░░░░░░░░░░░ 40% (2 tasks, 16/40 subtasks)
✅ Completed: ████████████████████ 100% (3 tasks, 50/50 subtasks)

Time Tracking:
⏱️  Estimated: 120 hours
⏰ Actual: 67 hours (56% efficiency)
⏳ Remaining: ~53 hours

Velocity:
📈 Last 7 days: 3.5 tasks/day
📅 Est. completion: 12 days (2025-01-18)

Task Distribution:
🔴 High Priority:   45% progress (8 tasks)
🟡 Medium Priority: 62% progress (5 tasks)
🟢 Low Priority:    30% progress (3 tasks)
```

### Detailed Format
```
📊 Detailed Task Progress

🎯 FOCUS (1 task)
└── TASK-001: User Authentication
    Progress: ████████████░░░░░░░░ 60% (6/10)
    Time: 4h actual / 8h estimated
    Status: In Progress | Priority: High

📂 ACTIVE (5 tasks)
├── TASK-002: API Documentation
│   Progress: ░░░░░░░░░░░░░░░░░░░░ 0% (0/8)
│   Time: 0h actual / 4h estimated
│   Status: Pending | Priority: Medium
│
├── TASK-003: Search Implementation
│   Progress: ████░░░░░░░░░░░░░░░░ 20% (2/10)
│   Time: 2h actual / 12h estimated  
│   Status: In Progress | Priority: High
│
└── [... more tasks ...]

[Similar sections for PAUSED and COMPLETED]
```

### Chart Format
```
📊 Progress Chart

        0%    25%    50%    75%    100%
Focus   |████████████░░░░░░░░| 60%
Active  |███████░░░░░░░░░░░░░| 35%
Paused  |████████░░░░░░░░░░░░| 40%
Complete|████████████████████| 100%

Daily Progress (Last 7 Days):
Mon ██████ 6 tasks
Tue ████ 4 tasks  
Wed ███████ 7 tasks
Thu ███ 3 tasks
Fri █████ 5 tasks
Sat ██ 2 tasks
Sun ████ 4 tasks

Priority Distribution:
High   ████████████ 8 tasks (45% complete)
Medium ████████ 5 tasks (62% complete)
Low    █████ 3 tasks (30% complete)
```

## Grouping Options

### By Priority
Show progress grouped by high/medium/low priority

### By Status  
Group by pending/in_progress/completed/blocked

### By Assignee
If assignees are used, group by @mentions

### By Week
Show weekly progress trends

## Error Handling

- If no tasks found: Show setup instructions
- If task corrupted: Skip with warning, continue
- If no progress data: Show 0% with explanation

## Example

```bash
# Quick summary
task-progress

# Detailed view of all tasks
task-progress --format detailed

# Progress by priority
task-progress --by priority

# Visual charts
task-progress --format chart

# Export data
task-progress --format json > progress.json
```

## Implementation Tips for Claude Code

1. **Cache Calculations**: Parse once, calculate multiple views
2. **Visual Progress**: Use Unicode blocks for progress bars
3. **Smart Rounding**: Round percentages sensibly
4. **Trend Analysis**: Calculate velocity over different periods
5. **Color Coding**: Use ANSI colors if terminal supports
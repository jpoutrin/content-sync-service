# task-validate

**Description**: Validate task file format and consistency

**Category**: Task Management

**Source**: `claude_settings/python/shared/processes/task-file-management.md`

## Usage

```bash
task-validate <task-file> [--fix] [--strict]
```

## Arguments

- `<task-file>`: Required - Path to task file to validate
- `--fix`: Optional - Automatically fix common issues
- `--strict`: Optional - Apply strict validation rules

## Execution Instructions for Claude Code

When this command is run, Claude Code should:

1. Check file exists and is readable
2. Validate YAML header:
   - Required fields: task_id, title, status, priority, created
   - Field formats and values
   - Date formats (YYYY-MM-DD)
3. Validate task structure:
   - Proper markdown formatting
   - Task numbering consistency
   - Checkbox format validity
   - Progress calculation accuracy
4. Check metadata consistency:
   - Progress matches completed tasks
   - Hours tracking adds up
   - Dependencies exist
   - Status aligns with progress
5. If --fix, automatically correct issues
6. Generate detailed validation report

## Validation Rules

### Header Validation
```yaml
Required fields:
- task_id: Format TASK-XXX
- title: Non-empty string
- status: pending|in_progress|completed|blocked
- priority: high|medium|low
- created: Valid date

Optional fields:
- estimated_hours: Positive number
- actual_hours: Positive number
- assignee: String starting with @
- dependencies: Array of task IDs
- blocked_reason: Required if blocked
```

### Task Structure Rules

1. **Numbering**: Sequential, hierarchical
   ```
   ✅ 1.0, 1.1, 1.2, 2.0, 2.1
   ❌ 1.0, 1.2, 2.0 (missing 1.1)
   ```

2. **Checkbox Format**:
   ```
   ✅ - [ ] Task
   ✅ - [x] Task  
   ✅ - [-] Task
   ❌ - [] Task (missing space)
   ❌ * [ ] Task (wrong bullet)
   ```

3. **Progress Calculation**:
   ```
   Total = All - Cancelled
   Completed = [x] + ([-] * 0.5)
   Progress = (Completed / Total) * 100
   ```

## Auto-Fix Capabilities

With `--fix`:
- Add missing header fields with defaults
- Fix checkbox spacing
- Recalculate progress percentage
- Update last_updated date
- Fix task numbering gaps
- Normalize status values

## Output Format

```
🔍 Validating: TASK-001-user-authentication.md

📋 Header Validation:
✅ task_id: TASK-001
✅ title: Implement User Authentication
✅ status: in_progress
✅ priority: high
⚠️  estimated_hours: Missing (recommended)
✅ created: 2025-01-05
❌ dependencies: TASK-999 not found

📄 Structure Validation:
✅ Task numbering: Valid (1.0-4.2)
✅ Checkbox format: All valid
⚠️  Task 2.3: Missing time estimate
✅ Indentation: Consistent

📊 Consistency Checks:
❌ Progress mismatch: Header shows 50%, calculated 40%
✅ Status matches progress (in_progress)
⚠️  Actual hours (4h) approaching estimate (8h)

🔧 Auto-fixable issues: 2
- Progress percentage
- Missing estimated_hours field

Run with --fix to automatically correct these issues.

Summary: 2 errors, 3 warnings
```

## Strict Mode

Additional checks with `--strict`:
- All tasks have time estimates
- Work log entries for each session
- Dependencies properly documented
- No tasks without descriptions
- Blocked tasks have unblock criteria

## Error Handling

- If file not found: Clear error with path
- If not a task file: Warn but attempt validation
- If YAML corrupted: Show parse error location
- If --fix fails: Create .bak backup first

## Example

```bash
# Basic validation
task-validate tasks/active/TASK-001.md

# Validate and fix issues
task-validate tasks/focus/auth-task.md --fix

# Strict validation for review
task-validate TASK-002-api.md --strict

# Validate all tasks in a directory
for f in tasks/active/*.md; do task-validate "$f"; done
```

## Implementation Tips for Claude Code

1. **Parse Safely**: Handle malformed YAML gracefully
2. **Line Numbers**: Show line numbers for issues
3. **Backup Always**: Create .bak before any fixes
4. **Fix Order**: Apply fixes in safe order (metadata before content)
5. **Diff Display**: Show what --fix would change
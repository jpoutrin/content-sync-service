# task-unfocus

**Description**: End focus session and move task to appropriate directory

**Category**: Task Management

**Source**: `claude_settings/python/shared/processes/focused-task-management.md`

## Usage

```bash
task-unfocus [--pause|--complete|--active] [--reason <reason>]
```

## Arguments

- `--pause`: Move task to paused directory
- `--complete`: Move task to completed directory  
- `--active`: Move task back to active directory (default)
- `--reason`: Reason for pausing or note for completion

## Execution Instructions for Claude Code

When this command is run, Claude Code should:

1. Verify there's a task in focus/ directory
2. Perform final synchronization from TodoTools to file
3. Update task metadata:
   - Calculate total session time
   - Update actual_hours
   - Update last_updated
   - Add session summary to work log
4. Based on flags, move task to appropriate directory:
   - `--pause`: Move to paused/ with reason
   - `--complete`: Verify 100% done, move to completed/
   - Default: Move to active/
5. Clear TodoTools state
6. Generate session summary

## Session Summary Format

Add to work log:
```markdown
### 2025-01-06 14:30-16:45 - SESSION END (2.25h)
- Progress: 40% → 60% (+20%)
- Completed: Tasks 2.3, 2.4
- Status: Paused - Switching to urgent bugfix
- Next: Continue with 2.5 API integration
```

## Output Format

```
🔚 Ending focus session...

📊 Session Summary:
   Task: TASK-001 User Authentication
   Duration: 2 hours 15 minutes
   Progress: 40% → 60% (+20%)
   Tasks completed: 2

✅ Final sync complete
📝 Work log updated

📁 Moving task to: paused/
   Reason: Switching to urgent bugfix

💾 Task saved to: tasks/paused/TASK-001-auth.md

✨ Focus session ended successfully!
```

## Completion Validation

If `--complete` flag:
1. Check all subtasks are [x] or [~]
2. Verify no [-] in-progress tasks
3. Calculate final metrics
4. Add completion metadata

## Error Handling

- If no task in focus: Show message "No task currently in focus"
- If task not 100% but --complete: Ask for confirmation
- If sync fails: Show error but continue move
- If target directory missing: Create it

## Example

```bash
# Pause current task
task-unfocus --pause --reason "Waiting for API specs"

# Complete current task
task-unfocus --complete

# Just move back to active (default)
task-unfocus

# End with custom note
task-unfocus --reason "Blocked on database migration"
```

## Implementation Tips for Claude Code

1. **Atomic Operations**: Sync, then move to prevent data loss
2. **Session Tracking**: Calculate accurate session duration
3. **State Cleanup**: Ensure TodoTools fully cleared
4. **Graceful Degradation**: Move file even if sync fails
5. **Backup Creation**: Keep recent backup in case of issues
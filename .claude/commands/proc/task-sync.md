# task-sync

**Description**: Synchronize TodoTools with task files

**Category**: Task Management  

**Source**: `claude_settings/python/shared/processes/task-file-management.md`

## Usage

```bash
task-sync [--direction <direction>] [--force]
```

## Arguments

- `--direction`: Optional - Sync direction: auto, tools-to-file, file-to-tools (default: auto)
- `--force`: Optional - Force sync even if timestamps match

## Execution Instructions for Claude Code

When this command is run, Claude Code should:

1. **Auto Direction** (default):
   - Compare TodoTools state with task file
   - Detect which has newer changes
   - Sync from newer to older

2. **Tools-to-File Direction**:
   - Read current TodoTools state via TodoRead
   - Find corresponding task file in focus/
   - Update task file checkboxes based on todo status
   - Update progress percentage
   - Add sync entry to work log

3. **File-to-Tools Direction**:
   - Parse task file in focus/
   - Clear current todos
   - Load all tasks into TodoWrite
   - Preserve any in-memory-only state

4. Update sync metadata in both systems
5. Validate sync completed successfully

## Synchronization Rules

### Status Mapping
```python
# TodoTools → File
"pending" → "[ ]"
"in_progress" → "[-]"
"completed" → "[x]"

# File → TodoTools  
"[ ]" → "pending"
"[-]" → "in_progress"
"[x]" → "completed"
"[~]" → skip (cancelled)
```

### Progress Calculation
```python
completed = count("[x]")
in_progress = count("[-]") * 0.5
total = count(all_tasks) - count("[~]")
progress = ((completed + in_progress) / total) * 100
```

### Work Log Update
```markdown
### 2025-01-06 15:45 - SYNC
- Direction: tools-to-file
- Updated: 3 task statuses
- Progress: 40% → 50%
```

## Output Format

```
🔄 Synchronizing task state...

📍 Focus Task: TASK-001-user-authentication.md
📊 Sync Direction: Auto-detected (tools-to-file)

Comparing states:
- TodoTools last update: 15:42
- Task file last update: 15:30
→ TodoTools is newer, syncing to file

✅ Updates applied:
- Task 2.3: pending → completed
- Task 2.4: pending → in_progress
- Progress: 40% → 50%

📝 Work log updated
✅ Sync complete!
```

## Sync Validation

After sync, verify:
1. Todo count matches task count (excluding cancelled)
2. Status mappings are consistent
3. Progress calculation is correct
4. No data was lost

## Error Handling

- If no task in focus: Error - run `task-focus` first
- If file corrupted: Create backup, attempt repair
- If todos empty: Prompt to load from file
- If conflict: Show both states, ask user to choose

## Example

```bash
# Auto-sync (most common)
task-sync

# Force sync from TodoTools to file
task-sync --direction tools-to-file

# Force reload from file
task-sync --direction file-to-tools --force

# Check sync status without syncing
task-sync --dry-run
```

## Implementation Tips for Claude Code

1. **Timestamp Tracking**: Use file mtime and internal todo timestamps
2. **Atomic Writes**: Write to temp file, then move to prevent corruption
3. **Backup First**: Keep .bak file before any sync operation
4. **Merge Conflicts**: If both changed, merge intelligently or ask user
5. **Validation**: Always validate post-sync state matches expectations
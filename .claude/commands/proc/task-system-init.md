# task-system-init

**Description**: Initialize task management directory structure

**Category**: Task Management

**Source**: `claude_settings/python/shared/processes/task-file-management.md`

## Usage

```bash
task-system-init [--base-dir <directory>]
```

## Arguments

- `--base-dir`: Optional - Base directory for task system (default: current directory)

## Execution Instructions for Claude Code

When this command is run, Claude Code should:

1. Create the complete task management directory structure
2. Generate initial README files in each directory explaining its purpose
3. Create a `.gitkeep` file in each empty directory
4. Set up the focus tracking file
5. Display the created structure and next steps

## Directory Structure to Create

```
tasks/
├── focus/           # Current work in progress (WIP)
│   └── README.md    # Explains focus workflow
├── active/          # All active tasks not in focus
│   └── README.md
├── paused/          # Tasks paused for context switch
│   └── README.md
├── completed/       # Recently completed tasks
│   └── README.md
├── archive/         # Long-term storage
│   ├── 2025/
│   ├── 2024/
│   └── README.md
└── .task-config     # Task system configuration
```

## README Content for Each Directory

### focus/README.md
```markdown
# Focus Directory

This directory contains the current task file being actively worked on.
Only ONE task file should be in focus at a time.

## Workflow
1. Move task file here when starting work: `mv ../active/task.md .`
2. Work on the task using TodoRead/TodoWrite tools
3. When complete or pausing, move to appropriate directory
```

### active/README.md
```markdown
# Active Tasks

This directory contains all active task files that are not currently in focus.
Tasks here are approved and ready to work on.

## Moving Tasks
- To focus: `mv task.md ../focus/`
- To pause: `mv task.md ../paused/`
- When complete: `mv task.md ../completed/`
```

### paused/README.md
```markdown
# Paused Tasks

Tasks that were in progress but paused due to:
- Context switching to higher priority work
- Waiting for external dependencies
- Need for additional clarification

Include pause reason in task file header.
```

### completed/README.md
```markdown
# Completed Tasks

Recently completed tasks (last 30 days).
Tasks here should be archived monthly.

Archive with: `task-archive-completed --month 2025-01`
```

### Configuration File (.task-config)
```json
{
  "version": "1.0",
  "created": "2025-01-06",
  "settings": {
    "auto_sync": true,
    "sync_interval": "immediate",
    "archive_after_days": 30,
    "focus_limit": 1,
    "task_id_format": "sequential"
  },
  "last_task_id": 0
}
```

## Output Format

```
🎯 Initializing Task Management System...

📁 Creating directory structure:
   ✅ tasks/
   ✅ tasks/focus/
   ✅ tasks/active/
   ✅ tasks/paused/
   ✅ tasks/completed/
   ✅ tasks/archive/
   ✅ tasks/archive/2025/
   ✅ tasks/archive/2024/

📄 Creating documentation:
   ✅ focus/README.md
   ✅ active/README.md
   ✅ paused/README.md
   ✅ completed/README.md
   ✅ archive/README.md

⚙️  Creating configuration:
   ✅ .task-config

✅ Task system initialized successfully!

Next steps:
1. Generate tasks from PRD: `generate-tasks <prd-file>`
2. Start focused work: `task-focus <task-file>`
3. List all tasks: `task-list`
```

## Error Handling

- If `tasks/` already exists: Ask to reinitialize or skip
- If permission denied: Suggest using appropriate permissions
- If in git repo: Add `.gitkeep` files for empty directories

## Example

```bash
# Initialize in current directory
task-system-init

# Initialize in specific directory
task-system-init --base-dir ~/projects/myapp

# Reinitialize existing system
task-system-init --force
```

## Implementation Tips for Claude Code

1. **Check Existing**: Detect if system already initialized
2. **Git Integration**: Add `.gitkeep` for empty dirs if in git repo
3. **Permissions**: Create with appropriate read/write permissions
4. **Validation**: Ensure all directories created successfully
5. **Configuration**: Make config file human-editable JSON
# organize-prds

**Description**: Move PRDs to proper directory structure based on their status

**Category**: Product & Strategy

**Source**: `claude_settings/python/shared/processes/prd-management.md`

## Usage

```bash
organize-prds [--dry-run] [--create-dirs]
```

## Arguments

- `--dry-run`: Optional - Show what would be moved without actually moving files
- `--create-dirs`: Optional - Create missing directories if they don't exist (default: true)

## Execution Instructions for Claude Code

When this command is run, Claude Code should:

1. Create the standard PRD directory structure if it doesn't exist (unless --create-dirs=false)
2. Search for all `.md` files that match PRD naming patterns (*-prd.md, *-frd.md, *-simple-frd.md)
3. Read the YAML metadata header from each PRD file to determine status
4. Determine the correct directory based on:
   - Status (draft, review, approved, active, complete, archived)
   - Type (product-prds for *-prd.md, feature-prds for *-frd.md and *-simple-frd.md)
5. If --dry-run, show what would be moved
6. Otherwise, move files to their proper locations using git mv (if in git repo) or regular mv
7. Update any relative path references in the PRD if needed
8. Report summary of actions taken

## Directory Mapping

```
Status: DRAFT     → Keep in current location (user's workspace)
Status: REVIEW    → product-docs/prds/review/
Status: APPROVED  → product-docs/prds/approved/
Status: ACTIVE    → product-docs/prds/active/[product-prds|feature-prds]/
Status: COMPLETE  → product-docs/prds/archive/YYYY/
Status: ARCHIVED  → product-docs/prds/archive/YYYY/
```

## Output Format

```
🗂️  Organizing PRDs...

✅ Created directory structure:
   - product-docs/prds/active/product-prds/
   - product-docs/prds/active/feature-prds/
   - product-docs/prds/review/
   - product-docs/prds/approved/
   - product-docs/prds/archive/2025/

📄 Moving PRDs:
   - user-auth-frd.md → product-docs/prds/active/feature-prds/ (Status: ACTIVE)
   - inventory-prd.md → product-docs/prds/review/ (Status: REVIEW)
   - old-feature-frd.md → product-docs/prds/archive/2024/ (Status: ARCHIVED)

📊 Summary:
   - Files moved: 3
   - Files skipped (DRAFT): 2
   - Errors: 0

✅ Organization complete!
```

## Error Handling

- If file already exists at destination: Skip and report conflict
- If metadata is missing: Skip file and report as "needs manual review"
- If not in a git repository: Use regular mv command instead of git mv
- If permission denied: Report error and continue with other files

## Example

```bash
# Organize all PRDs
organize-prds

# See what would be moved without actually moving
organize-prds --dry-run

# Organize without creating new directories
organize-prds --create-dirs=false
```

## Implementation Tips for Claude Code

1. **Git Integration**: Check if in git repo first, use `git mv` if available
2. **Path Updates**: Update relative paths in task_file references after moving
3. **Batch Operations**: Collect all moves first, then execute for better performance
4. **Validation**: Verify source files exist and destination directories are writable
5. **Status Detection**: Handle missing or malformed metadata gracefully
6. **Archive Year**: Extract year from last_updated or use current year for archiving
# prd-check

**Description**: Validate PRD format, metadata, and completeness

**Category**: Product & Strategy

**Source**: `claude_settings/python/shared/processes/prd-management.md`

## Usage

```bash
prd-check <prd-file> [--fix] [--strict]
```

## Arguments

- `<prd-file>`: Required - Path to the PRD file to validate
- `--fix`: Optional - Automatically fix common issues where possible
- `--strict`: Optional - Apply strict validation rules for production PRDs

## Execution Instructions for Claude Code

When this command is run, Claude Code should:

1. Read the specified PRD file
2. Validate the YAML metadata header:
   - Check for required fields (status, version, created, last_updated, author)
   - Validate field formats (dates, version numbers, status values)
   - Check for conditional fields (approved_by when status is APPROVED)
3. Validate PRD structure based on type:
   - Product PRD: Should have all 15 sections
   - Feature PRD: Should have all 12 sections
   - Simple Feature PRD: Should have all 7 sections
4. Check content quality:
   - Sections not empty
   - Minimum content length for key sections
   - No placeholder text (e.g., "TBD", "TODO", "[Add content here]")
5. Validate references:
   - Task file exists if referenced
   - Relative paths are correct
   - Links to other documents are valid
6. If --fix flag is set, automatically fix common issues
7. Generate detailed validation report

## Validation Rules

### Metadata Validation
- **Required Fields**: status, version, created, last_updated, author
- **Status Values**: Must be one of: DRAFT, REVIEW, APPROVED, ACTIVE, COMPLETE, ARCHIVED
- **Date Format**: YYYY-MM-DD
- **Version Format**: Semantic versioning (e.g., 1.0, 2.1.3)

### Structure Validation

**Product PRD Sections** (15 required):
1. Executive Summary
2. Problem Statement
3. Objectives and Goals
4. User Personas
5. User Requirements
6. Functional Requirements
7. Non-Functional Requirements
8. User Journey
9. Technical Considerations
10. Success Metrics
11. Risks and Mitigations
12. Timeline and Milestones
13. Dependencies
14. Open Questions
15. Appendices

**Feature PRD Sections** (12 required):
1. Feature Overview
2. Problem Statement
3. Objectives
4. User Stories
5. Functional Requirements
6. Non-Functional Requirements
7. User Interface
8. Technical Design
9. Success Metrics
10. Risks
11. Timeline
12. Dependencies

**Simple Feature PRD Sections** (7 required):
1. Feature Summary
2. Problem & Solution
3. User Stories
4. Requirements
5. Technical Notes
6. Success Criteria
7. Timeline

### Content Quality Checks
- Each section has minimum 50 characters (except Appendices)
- No placeholder text patterns
- Status history exists if status is not DRAFT
- Implementation tracking section exists if status is ACTIVE

## Auto-Fix Capabilities

With `--fix` flag, automatically:
- Add missing metadata fields with defaults
- Fix date formats
- Create empty sections for missing structure
- Update last_updated to current date
- Add status history section
- Fix common typos in section headers

## Output Format

```
🔍 Validating PRD: user-authentication-frd.md

📋 Metadata Check:
✅ status: ACTIVE
✅ version: 1.2
✅ created: 2025-01-01
⚠️  last_updated: 2024-12-15 (outdated - 22 days old)
✅ author: John Doe
❌ task_file: Missing required field for ACTIVE status

📄 Structure Check (Feature PRD - 12 sections required):
✅ 1. Feature Overview (245 chars)
✅ 2. Problem Statement (189 chars)
❌ 3. Objectives - MISSING
✅ 4. User Stories (567 chars)
⚠️  5. Functional Requirements (42 chars - below minimum)
[...]

🔗 Reference Check:
❌ Task file not found: ./tasks/user-auth-tasks.md
✅ Persona reference valid: ../personas/developer-persona.md

📝 Content Quality:
⚠️  Found placeholder text in section 8: "TODO: Add technical design"
⚠️  Empty section: Dependencies

📊 Validation Summary:
- Critical Issues: 3
- Warnings: 4
- Passed Checks: 15

❌ VALIDATION FAILED - Fix critical issues before proceeding

Suggested fixes:
1. Add missing 'Objectives' section
2. Create task file or update reference
3. Expand 'Functional Requirements' content
4. Replace placeholder text in 'Technical Design'

Run with --fix to automatically address some issues.
```

## Error Handling

- If file not found: Exit with clear error message
- If not a PRD file: Warn but continue validation
- If YAML parse error: Show line number and error details
- If --fix creates issues: Backup original file first

## Example

```bash
# Basic validation
prd-check user-authentication-frd.md

# Validate and auto-fix issues
prd-check user-authentication-frd.md --fix

# Strict validation for production PRD
prd-check inventory-system-prd.md --strict

# Check a draft PRD
prd-check ./drafts/new-feature-frd.md
```

## Implementation Tips for Claude Code

1. **YAML Parsing**: Handle both missing and malformed metadata gracefully
2. **Section Detection**: Use regex to find markdown headers flexibly
3. **Backup Creation**: Always create .bak file before --fix modifications
4. **Detailed Reporting**: Show line numbers for issues when possible
5. **Exit Codes**: Return 0 for pass, 1 for warnings only, 2 for failures
6. **Progressive Validation**: Check critical issues first, stop if fundamental problems
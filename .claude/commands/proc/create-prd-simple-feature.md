# create-prd-simple-feature

**Description**: Streamlined PRD creation for simple features with limited business complexity

**Category**: Product & Strategy

**Source**: `claude_settings/python/shared/templates/prd-simple-feature-template.md`

## Usage

```bash
create-prd-simple-feature <feature-name>
```

## Arguments

- `<feature-name>`: Required - The name of the feature (will be used for filename and document title)

## Execution Instructions for Claude Code

When this command is run, Claude Code should:

1. Read the simplified template from `claude_settings/python/shared/templates/prd-simple-feature-template.md`
2. Start a streamlined interactive session (15-20 minutes)
3. Focus on essential implementation details
4. Generate a concise PRD suitable for 3-10 day features
5. Save the document as `<feature-name>-simple-frd.md`

## Interactive Session Flow

The session is optimized for speed and clarity:

### 1. **Feature Overview** [Section 1 of 7]
- "Feature name confirmation: [prefilled with argument]"
- "Which product/system does this belong to?"
- "Describe this feature and its business value (2-3 sentences):"
- "What problem does it solve? (1 paragraph):"
- "Effort estimate - XS (1-2 days), S (3-5 days), or M (6-10 days):"

### 2. **User Story & Acceptance** [Section 2 of 7]
- "Write the user story (As a... I want to... So that...):"
- "List acceptance criteria (use Given/When/Then format):"
  
  Provide template:
  ```
  Given: [initial context]
  When: [action taken]
  Then: [expected result]
  ```
- "Describe 2-3 main usage scenarios (brief steps):"
- "Any important edge cases? (or type 'none'):"

### 3. **Functional Specs** [Section 3 of 7]
- "List the core functionality (bullet points):"
- "Define inputs and outputs:"
  
  Example format:
  ```
  Input: user_id (integer), filter_type (string: 'active'|'all')
  Output: JSON array of user objects
  ```
- "Key business rules (if any):"
- "What data is needed and where from?"

### 4. **Technical Implementation** [Section 4 of 7]
- "API endpoints needed? (provide method, path, and brief description or 'none'):"
  
  Example:
  ```
  GET /api/v1/users/{id}/settings - Retrieve user settings
  PUT /api/v1/users/{id}/settings - Update user settings
  ```
- "Database changes? (new columns, tables, or 'none'):"
- "UI components needed (list them):"
- "Technical approach in 2-3 sentences:"

### 5. **Task Breakdown** [Section 5 of 7]
Ask for simple task list:
- "Backend development tasks (2-5 tasks):"
- "Frontend development tasks (2-5 tasks):"
- "Testing tasks (1-3 tasks):"

Format guide:
```
- [ ] Task description (Xh)
- [ ] Another task (Xh)
```

### 6. **Testing Requirements** [Section 6 of 7]
- "List 3-5 key test scenarios:"
- "Write 2-3 acceptance tests (what user actions to verify):"

### 7. **Rollout & Demo** [Section 7 of 7]
- "Simple rollout plan (1-2 sentences):"
- "Demo steps (3-5 bullet points showing the feature):"
- "Any blockers or dependencies? (or type 'none'):"
- "Ticket/issue number (if exists):"

## Output Format

Generate a concise document that:
- Fits on 2-3 pages
- Can be read in 5 minutes
- Contains enough detail for implementation
- Focuses on the "what" and "how"
- Includes clear tasks ready for sprint planning

## When to Use This vs Full Feature PRD

**Use Simple Feature PRD for:**
- Adding new fields or filters
- Simple CRUD operations
- UI enhancements
- Basic integrations
- Small workflow improvements
- Features under 10 days effort

**Use Full Feature PRD for:**
- Complex business logic
- Multiple user personas
- System architecture changes
- High-risk features
- Features over 10 days effort
- External stakeholder involvement

## Quick Tips for Claude Code

1. Keep questions concise and combined
2. Provide format examples inline
3. Allow "none" for optional items
4. Pre-calculate total effort from tasks
5. Suggest common patterns
6. Skip sections if not applicable
7. Aim for 15-20 minute completion time

## Example Usage

```bash
create-prd-simple-feature add-user-filter
```

This creates `add-user-filter-simple-frd.md` ready for sprint planning.

## Session Management

- Show progress: "Section X of 7"
- Allow quick edits before finalizing
- Provide summary of what was captured
- Confirm save location
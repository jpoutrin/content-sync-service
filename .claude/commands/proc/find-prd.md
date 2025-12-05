# find-prd

**Description**: Search PRDs by content, title, or metadata

**Category**: Product & Strategy

**Source**: `claude_settings/python/shared/processes/prd-management.md`

## Usage

```bash
find-prd <search-term> [--type <type>] [--status <status>] [--author <name>]
```

## Arguments

- `<search-term>`: Required - Text to search for in PRD content or metadata
- `--type`: Optional - Filter by PRD type (product, feature, simple)
- `--status`: Optional - Filter by status (draft, review, approved, active, complete, archived)
- `--author`: Optional - Filter by author name

## Execution Instructions for Claude Code

When this command is run, Claude Code should:

1. Search for PRD files in common locations:
   - Current directory and subdirectories
   - `product-docs/` directory structure
   - Any `*.prd.md`, `*.frd.md`, or `*.simple-frd.md` files
2. For each PRD file found:
   - Search for the search term in the file content (case-insensitive)
   - Extract metadata to check against filters
   - Calculate relevance score based on matches
3. Apply any specified filters (type, status, author)
4. Sort results by relevance (number of matches) and recency
5. Display results with context snippets
6. Show file paths relative to current directory when possible

## Search Scoring

Calculate relevance score based on:
- Title match: 10 points
- Metadata match: 5 points  
- Content match: 1 point per occurrence
- Recency bonus: Higher score for recently updated files

## Output Format

```
🔍 Searching for "authentication" in PRDs...

Found 3 matching PRDs:

📄 [1] user-authentication-frd.md (Score: 25)
   Path: product-docs/prds/active/feature-prds/user-authentication-frd.md
   Status: ACTIVE | Author: John Doe | Updated: 2025-01-06
   
   Matches:
   Line 5: "# User Authentication System"
   Line 42: "...implement OAuth2 authentication with JWT tokens..."
   Line 78: "...two-factor authentication must be optional..."

📄 [2] api-gateway-prd.md (Score: 12)
   Path: product-docs/prds/review/api-gateway-prd.md
   Status: REVIEW | Author: Jane Smith | Updated: 2025-01-05
   
   Matches:
   Line 156: "...integrate with authentication service..."
   Line 203: "...pass authentication headers to downstream..."

📄 [3] mobile-app-simple-frd.md (Score: 8)
   Path: ./drafts/mobile-app-simple-frd.md
   Status: DRAFT | Author: Bob Wilson | Updated: 2025-01-03
   
   Matches:
   Line 89: "...use biometric authentication where available..."

Total: 3 PRDs found matching "authentication"
```

## Error Handling

- If no PRDs found: Suggest checking search term or running `list-prds`
- If search term too short (< 2 chars): Request longer search term
- If invalid filter values: Show valid options
- If file read error: Skip file and note in results

## Example

```bash
# Search for authentication in all PRDs
find-prd authentication

# Search for API in active feature PRDs
find-prd API --type feature --status active

# Find all PRDs by John Doe containing "payment"
find-prd payment --author "John Doe"

# Search for security requirements in product PRDs
find-prd security --type product
```

## Implementation Tips for Claude Code

1. **Efficient Search**: Use grep or ripgrep for fast content searching
2. **Context Extraction**: Show 1-2 lines around each match for context
3. **Path Resolution**: Show shortest meaningful path to each file
4. **Fuzzy Matching**: Consider partial matches in metadata fields
5. **Performance**: For large codebases, limit search depth or use indexing
6. **Highlighting**: If terminal supports it, highlight search terms in output
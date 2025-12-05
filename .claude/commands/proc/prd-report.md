# prd-report

**Description**: Generate comprehensive summary report of all PRDs

**Category**: Product & Strategy

**Source**: `claude_settings/python/shared/processes/prd-management.md`

## Usage

```bash
prd-report [--output <file>] [--format <format>]
```

## Arguments

- `--output`: Optional - Save report to file instead of displaying
- `--format`: Optional - Report format (markdown, html, json). Default: markdown

## Execution Instructions for Claude Code

When this command is run, Claude Code should:

1. Scan all PRD directories to find all PRD files
2. Extract metadata and calculate statistics for each PRD
3. Generate comprehensive analytics including:
   - Total PRD count by type and status
   - Implementation progress for active PRDs
   - Timeline analysis (creation, approval, completion rates)
   - Author contribution statistics
   - Average time in each status
   - Bottleneck identification
4. Create visualizations using ASCII charts or markdown tables
5. Identify potential issues (stale PRDs, missing metadata, broken links)
6. Output report in requested format

## Report Sections

### 1. Executive Summary
- Total PRDs and breakdown by type
- Overall implementation progress
- Key metrics and KPIs

### 2. Status Distribution
- PRD count by status with percentages
- Visual representation (bar chart)
- Status transition metrics

### 3. Implementation Progress
- Active PRDs with completion percentages
- Estimated completion dates
- Blocked or stalled PRDs

### 4. Timeline Analysis
- Average time from creation to approval
- Average implementation duration
- Age distribution of PRDs

### 5. Author Analytics
- PRDs per author
- Success rate by author
- Active contributions

### 6. Health Check
- PRDs missing metadata
- Stale PRDs (no updates > 30 days)
- Broken task file links
- PRDs in wrong directories

## Output Format Example

```markdown
# PRD Management Report
Generated: 2025-01-06

## Executive Summary

**Total PRDs**: 24
- Product PRDs: 4 (17%)
- Feature PRDs: 15 (62%)
- Simple Feature PRDs: 5 (21%)

**Overall Implementation Progress**: 58% (Active PRDs)

## Status Distribution

```
DRAFT     ████████ 8 (33%)
REVIEW    ████ 4 (17%)
APPROVED  ██ 2 (8%)
ACTIVE    ██████ 6 (25%)
COMPLETE  ███ 3 (12%)
ARCHIVED  █ 1 (4%)
```

## Active PRD Progress

| PRD Name | Type | Progress | Days Active | Est. Completion |
|----------|------|----------|-------------|-----------------|
| user-auth-frd | Feature | 67% | 5 | 2025-01-09 |
| inventory-prd | Product | 45% | 12 | 2025-01-15 |
| search-frd | Feature | 90% | 3 | 2025-01-07 |

## Timeline Metrics

- **Avg Creation → Approval**: 3.2 days
- **Avg Approval → Complete**: 8.5 days
- **Longest Active PRD**: inventory-prd (12 days)

## Author Contributions

| Author | PRDs | Completed | Active | Success Rate |
|--------|------|-----------|--------|--------------|
| John Doe | 10 | 2 | 3 | 67% |
| Jane Smith | 8 | 1 | 2 | 50% |
| Bob Wilson | 6 | 0 | 1 | 0% |

## Health Check Issues

⚠️ **Missing Metadata**: 2 PRDs
- drafts/unnamed-prd.md (no status)
- old/legacy-feature.md (no header)

⚠️ **Stale PRDs** (>30 days): 3 PRDs
- api-redesign-prd.md (45 days in REVIEW)
- data-migration-frd.md (38 days in DRAFT)

❌ **Broken Task Links**: 1 PRD
- reporting-frd.md → ./tasks/reporting-tasks.md (not found)

## Recommendations

1. Review and update 3 stale PRDs
2. Fix metadata for 2 PRDs missing headers  
3. Archive 1 completed PRD from last quarter
4. Repair 1 broken task file link
```

## Error Handling

- If no PRDs found: Generate empty report with setup instructions
- If metadata parsing fails: Include file in health check section
- If task file not accessible: Mark as broken link

## Example

```bash
# Generate report to console
prd-report

# Save report to file
prd-report --output prd-report-2025-01.md

# Generate HTML report
prd-report --format html --output report.html

# Generate JSON data for further processing
prd-report --format json --output prd-data.json
```

## Implementation Tips for Claude Code

1. **Efficient Scanning**: Cache file reads to avoid multiple parses
2. **Progress Calculation**: Handle missing or invalid task files gracefully
3. **Date Handling**: Parse various date formats flexibly
4. **Visualization**: Use Unicode box drawing for charts in terminal
5. **Performance**: For large projects, show progress indicator during scan
6. **Export Formats**: Structure JSON output for easy integration with other tools
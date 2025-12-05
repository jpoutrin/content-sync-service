# capture-screenshot

**Description**: Capture screenshots of web pages for documentation

**Category**: Documentation & Testing

**Usage**: 
```bash
capture-screenshot <url> [options]
```

**Options**:
- `--mobile` - Use mobile viewport (375x667)
- `--full-page` - Capture entire page (default: viewport only)
- `--wait <seconds>` - Additional wait time after network idle

## Execution Instructions for Claude Code

When this command is run, Claude Code should:

1. **Validate Prerequisites**:
   - Check if Playwright MCP is configured
   - If not, suggest running: `claude-blueprint configure-mcp playwright`

2. **Parse Arguments**:
   - Extract URL (required)
   - Parse optional flags
   - Set defaults:
     - Viewport: 1920x1080 (desktop) or 375x667 (mobile)
     - Capture mode: viewport only (unless --full-page)
     - Wait strategy: network idle + optional wait time

3. **Prepare Directory**:
   - Ensure `./docs/screenshots/adhoc/` directory exists
   - Create it if necessary

4. **Generate Filename**:
   - Pattern: `{domain}_{timestamp}.png`
   - Example: `example-com_2025-01-13-143045.png`
   - Extract domain from URL (sanitized for filesystem)
   - Add timestamp for uniqueness

5. **Take Screenshot**:
   - Use Playwright MCP to navigate to URL
   - Apply viewport settings
   - Wait for network idle
   - Apply additional wait if specified
   - Capture screenshot (viewport or full page)
   - MCP will save to a temporary location (look for "Screenshot saved at" or similar in output)
   - Extract the temporary file path from MCP output
   - Move the file from temporary location to `./docs/screenshots/adhoc/{generated_filename}`

6. **Save Metadata**:
   - Create JSON file with same base name
   - Include:
     - url: Original URL
     - timestamp: ISO timestamp
     - viewport: { width, height }
     - fullPage: boolean
     - filename: Screenshot filename
     - additionalWait: seconds (if used)

7. **Report Success**:
   - Show saved screenshot path
   - Display basic metadata
   - Suggest next steps if applicable

## Example Usage

```bash
# Basic screenshot
capture-screenshot https://example.com

# Mobile viewport with full page
capture-screenshot https://example.com --mobile --full-page

# With additional wait time
capture-screenshot https://example.com --wait 3
```

## Error Handling

- If URL is invalid: Show error and usage
- If Playwright MCP not configured: Provide setup instructions
- If screenshot fails: Show error details and common solutions
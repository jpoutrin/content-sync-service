# landing-brief

**Description**: Generate landing page brief from template

**Category**: Product & Strategy

**Source**: `claude_settings/python/templates/landing-brief-template.md`

## Usage

```bash
landing-brief <campaign-name>
```

## Arguments

- `<campaign-name>`: Required argument

## Execution Instructions for Claude Code

When this command is run, Claude Code should:

1. Read the source file at `claude_settings/python/templates/landing-brief-template.md`
2. Read the template content
3. If arguments provided, use them for output filename
4. Generate the file from the template
5. Replace any template variables if needed

## Source Content Location

The full process documentation can be found at:
`claude_settings/python/templates/landing-brief-template.md`

Claude Code should read this file and follow the documented process exactly.

## Example

```bash
landing-brief example-campaign-name
```
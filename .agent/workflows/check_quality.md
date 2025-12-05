---
description: Check code quality (Linting, Formatting, Typing)
---

# Quality Agent

This workflow ensures your Python code meets quality standards.

1. **Format Code**
   - Auto-formats code using `ruff`.
   // turbo
   ```bash
   uv run ruff format .
   ```

2. **Lint Code**
   - Checks for linting errors using `ruff`.
   // turbo
   ```bash
   uv run ruff check . --fix
   ```

3. **Type Check**
   - Checks static types using `mypy`.
   ```bash
   uv run mypy .
   ```

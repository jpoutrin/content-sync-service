---
description: Run the Python test suite
---

# Test Agent

This workflow runs the project's test suite using `pytest`.

1. **Run Tests**
   - Executes all tests with verbose output.
   ```bash
   uv run pytest -v
   ```

2. **Run Tests with Coverage** (Optional)
   - If you want to see coverage report.
   ```bash
   # uv run pytest --cov=.
   ```

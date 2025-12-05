---
description: Start the local Supabase development stack
---

# Start Supabase Agent

This workflow starts the local Supabase stack (Auth, DB, Studio, etc.).

1. **Check Prerequisites**
   - Checks if Docker is running.
   ```bash
   docker info > /dev/null 2>&1 || echo "Docker is not running!"
   ```

2. **Start Supabase**
   - Uses `npx` to run the Supabase CLI without installing it globally.
   // turbo
   ```bash
   npx supabase start
   ```

3. **Show Status**
   ```bash
   npx supabase status
   ```

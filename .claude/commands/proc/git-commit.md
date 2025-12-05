  Create a git commit with an automatically generated commit message based on the current changes.

  ## Process:

  1. **Check Git Configuration**
     - Verify current git user.name and user.email
     - If email is not "jpoutrin@productvista.fr", remind user to set it:
       ```bash
       git config user.email "jpoutrin@productvista.fr"
       git config user.name "jpoutrin"
       ```

  2. **Analyze Current Changes**
     - Run `git status` to see all changes
     - Run `git diff` to understand unstaged changes
     - Run `git diff --cached` to understand staged changes
     - Review the changes to understand what was modified

  3. **Generate Commit Message**
     - Analyze the changes at a high level
     - Create a concise commit message that:
       * Summarizes the main changes without being too detailed
       * Groups related changes together
       * Uses conventional commit format (feat:, fix:, refactor:, docs:, etc.)
       * Avoids mentioning Claude, Anthropic, or AI assistance
       * Focuses on WHAT changed and WHY, not implementation details

     Example format:
     ```
     type: Brief description of changes

     - High level change 1
     - High level change 2
     - High level change 3
     ```

  4. **Stage All Changes**
     - Run `git add -A` to stage all changes

  5. **Confirm Commit**
     - Display the proposed commit message
     - Ask user: "Proceed with this commit message? (yes/no)"
     - If yes, proceed to commit
     - If no, ask if they want to:
       a) Edit the message (let them provide a new one)
       b) Cancel the operation

  6. **Create Commit**
     - Execute: `git commit -m "message"`
     - Show confirmation that commit was created

  7. **Optional Push**
     - Ask: "Would you like to push to remote? (yes/no)"
     - If yes, run `git push`
     - If the branch has no upstream, suggest `git push -u origin branch-name`

  ## Important Notes:
  - NO mention of Claude, Anthropic, or AI in commit messages
  - Keep commit messages professional and focused
  - Use the user's actual name and email (jpoutrin@productvista.fr)
  - Focus on business value and changes, not technical implementation details

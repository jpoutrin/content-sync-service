  Set up a git repository with proper configuration, gitignore, and sensible defaults.

  ## Process:

  1. **Initialize Repository**
     - Check if `.git` directory exists
     - If not, ask: "No git repository found. Initialize one? (yes/no)"
     - If yes, run `git init`

  2. **Configure User Settings (Local)**
     Ask: "Configure git user as 'Jeremie Poutrin <jpoutrin@productvista.fr>'? (yes/no)"
     If yes:
     ```bash
     git config user.name "Jeremie Poutrin"
     git config user.email "jpoutrin@productvista.fr"
     ```

  3. **Set Default Branch**
     Ask: "Set default branch to 'master'? (yes/no)"
     If yes:
     ```bash
     git config init.defaultBranch master
     ```
     If current branch is not master, offer to rename it.

  4. **Configure VS Code Integration**
     Ask: "Configure VS Code as default editor and merge tool? (yes/no)"
     If yes:
     ```bash
     git config core.editor "code --wait"
     git config merge.tool vscode
     git config mergetool.vscode.cmd 'code --wait $MERGED'
     git config diff.tool vscode
     git config difftool.vscode.cmd 'code --wait --diff $LOCAL $REMOTE'
     ```

  5. **Set Up Git Aliases**
     Ask: "Add common git aliases? (yes/no)"
     If yes, configure:
     ```bash
     git config alias.co checkout
     git config alias.br branch
     git config alias.ci commit
     git config alias.st status
     git config alias.unstage 'reset HEAD --'
     git config alias.last 'log -1 HEAD'
     git config alias.visual '!gitk'
     git config alias.lg 'log --oneline --decorate --graph --all'
     git config alias.cm 'commit -m'
     git config alias.ca 'commit -am'
     git config alias.dc 'diff --cached'
     git config alias.aa 'add -A'
     git config alias.ff 'merge --ff-only'
     git config alias.pullff 'pull --ff-only'
     git config alias.noff 'merge --no-ff'
     git config alias.fa 'fetch --all'
     git config alias.pom 'push origin master'
     git config alias.b 'branch -v'
     git config alias.r 'remote -v'
     git config alias.t 'tag -l'
     git config alias.cp 'cherry-pick'
     git config alias.undo 'reset --soft HEAD~1'
     git config alias.amend 'commit --amend --no-edit'
     ```

  6. **Configure .gitignore**
     - Check if `.gitignore` exists
     - Auto-detect languages/frameworks in the repository:
       * Python: look for .py files, requirements.txt, setup.py, pyproject.toml
       * JavaScript/Node: package.json, .js files
       * TypeScript: tsconfig.json, .ts files
       * PHP: composer.json, .php files
       * Ruby: Gemfile, .rb files
       * Java: pom.xml, build.gradle, .java files
       * Go: go.mod, .go files
       * Rust: Cargo.toml, .rs files
       * .NET: .csproj, .cs files

     Ask: "Update .gitignore for detected languages [list detected]? (yes/no)"

     If yes, merge these patterns intelligently (don't duplicate):

     **Common patterns:**
     ```
     # OS Files
     .DS_Store
     Thumbs.db
     *.swp
     *.swo
     *~

     # IDE
     .vscode/
     .idea/
     *.iml
     .project
     .classpath
     .settings/

     # Environment
     .env
     .env.local
     .env.*.local
     ```

     **Language-specific patterns:**
     - Python: `__pycache__/`, `*.pyc`, `venv/`, `env/`, `.pytest_cache/`, `dist/`, `build/`, `*.egg-info/`
     - Node: `node_modules/`, `npm-debug.log`, `yarn-error.log`, `.npm/`
     - PHP: `vendor/`, `composer.lock` (optional)
     - Ruby: `bundle/`, `Gemfile.lock` (optional)
     - Java: `target/`, `*.class`, `*.jar`
     - Go: `bin/`, `pkg/`
     - Rust: `target/`, `Cargo.lock` (for libraries)
     - .NET: `bin/`, `obj/`, `*.user`

  7. **Additional Git Settings**
     Ask: "Configure additional git settings? (yes/no)"
     If yes:
     ```bash
     git config core.autocrlf input  # Unix line endings
     git config core.ignorecase false
     git config pull.rebase false    # merge (not rebase) on pull
     git config fetch.prune true     # remove deleted remote branches
     git config diff.colorMoved zebra # highlight moved code blocks
     git config rebase.autosquash true # auto squash fixup! commits
     ```

  8. **Summary**
     Display what was configured:
     - User: name and email
     - Default branch: master
     - Editor: VS Code (if configured)
     - Aliases: list of shortcuts (if added)
     - Gitignore: languages detected and added
     - Additional settings applied

  ## Notes:
  - All settings are local to this repository only
  - Existing .gitignore content is preserved and merged
  - Always ask for confirmation before making changes
  - Show what will be changed before applying

# Parallel Development Artifacts

This directory contains artifacts for parallel multi-agent development.

## Structure

Each Tech Spec decomposition creates a subdirectory:

```
parallel/
├── TS-0042-inventory-system/      # Keyed by Tech Spec ID
│   ├── manifest.json              # Regeneration metadata
│   ├── context.md                 # Shared project context
│   ├── tasks/                     # Task specifications
│   ├── contracts/                 # Shared types & API schema
│   ├── prompts/                   # Agent launch prompts
│   ├── scripts/                   # Launch & monitor scripts
│   ├── architecture.md            # System design
│   └── task-graph.md              # Dependency visualization
└── ...
```

## Commands

- `/parallel-decompose <prd> --tech-spec <ts-file>` - Decompose PRD into tasks
- `/parallel-integrate --parallel-dir <dir>` - Verify integration

## Regeneration

Each subdirectory contains a `manifest.json` with metadata to regenerate artifacts:
```bash
# Re-run decomposition with same args
/parallel-decompose docs/prd.md --tech-spec tech-specs/approved/TS-XXXX.md
```

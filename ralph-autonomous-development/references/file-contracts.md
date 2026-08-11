# Ralph File Contracts

## `prd.json`

Location: repository root.

Purpose: executable checklist and branch identity.

```json
{
  "project": "Feature Name",
  "branchName": "ralph/feature-name",
  "description": "Short summary",
  "userStories": [
    {
      "id": "US-001",
      "title": "Small story title",
      "description": "As a role, I want capability so that outcome.",
      "acceptanceCriteria": [
        "Concrete verifiable condition",
        "Typecheck passes",
        "Tests pass"
      ],
      "priority": 1,
      "passes": false,
      "notes": ""
    }
  ]
}
```

Rules:

- `branchName` should usually be `ralph/[feature-name]`.
- `priority` defines execution order.
- `passes` is the state machine.
- `notes` is for short status only; durable learning belongs in `progress.txt`.
- Do not encode the full architecture only in JSON.

## `progress.txt`

Location: repository root.

Purpose: durable memory between fresh agent runs.

Suggested header:

```text
# Ralph Progress: [Feature Name]

Started: YYYY-MM-DD
Source PRD: tasks/prd-[feature].md

## Codebase Patterns

- [Durable reusable pattern.]
```

Iteration entry:

```text
## YYYY-MM-DD HH:mm TZ - US-001
- Implemented ...
- Files changed:
  - `path/to/file`
- Validation:
  - `command`
- **Learnings for future iterations:**
  - [Gotcha or reusable pattern.]
---
```

Rules:

- Append; do not rewrite history during normal execution.
- Record failed validation honestly.
- Promote repeated gotchas into `Codebase Patterns`.
- Create this file before `scripts/ralph/ralph.sh --dry-run`; dry-run is a validator, not an initializer.

## `archive/`

Location: repository root.

Purpose: preserve previous Ralph runs before replacing root `prd.json`.

Suggested layout:

```text
archive/YYYY-MM-DD-feature-name/
  prd.json
  progress.txt
  prd-feature-name.md
```

Archive before starting a new run if the existing `prd.json.branchName` differs.

Create the directory before dry-run:

```bash
mkdir -p archive
```

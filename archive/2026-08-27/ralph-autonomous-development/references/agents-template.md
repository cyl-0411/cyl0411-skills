# `scripts/ralph/AGENTS.md` Template

Copy and customize this for the target repository.

```markdown
# Ralph Agent Instructions

You are an autonomous coding agent working in this repository.

## Your Task

1. Read `tasks/prd-[feature].md`, root `prd.json`, and `progress.txt`.
2. Read any referenced architecture docs named by the PRD.
3. Treat the PRD's Decisions, Non-Goals, Validation, and Risks as already hardened. Do not reopen them unless implementation proves a contradiction.
4. Check that you are on the branch from `prd.json` `branchName`. If not, check it out or create it from the current branch.
5. Pick the highest-priority user story where `passes: false`.
6. Implement that single user story only.
7. Run the checks required by the story. At minimum, run the repo's typecheck or equivalent.
8. If the story touches UI, verify it in a browser.
9. If the story touches runtime, release, infrastructure, or external integration behavior, run the real validation named in the PRD.
10. Update the source PRD and root `prd.json` to set the completed story `passes: true`.
11. Append your progress to `progress.txt`.
12. Commit all changes with message: `feat: [Story ID] - [Story Title]`, then push.

## Current Run Constraints

- Treat root `prd.json` as the executable story order.
- Treat the markdown PRD as authoritative for scope and behavior.
- Work on one story per iteration.
- Do not implement later stories opportunistically.
- Do not commit broken code.
- Do not skip required validation.
- Preserve unrelated user changes.

## Required Validation

Replace these examples with repo-specific commands:

```bash
npm run typecheck
npm test
```

Use focused tests for touched code. Use real integration validation where the PRD requires it.

## Progress Report Format

Append to `progress.txt`:

```text
## [Date/Time] - [Story ID]
- What was implemented
- Files changed
- Validation
- **Learnings for future iterations:**
  - Durable gotchas or reusable patterns
---
```

## Stop Condition

After completing a story, check whether all stories in `prd.json` have `passes: true`.

If all stories are complete and passing, reply with:

```text
<promise>COMPLETE</promise>
```

If any story remains incomplete, end normally so the next iteration can continue.
```

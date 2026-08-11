# PRD Authoring For Ralph

Write the PRD as an executable contract for future fresh agents.

Before writing, run `grill-me` or `grill-with-docs` to harden the plan. Copy the accepted conclusions into the PRD. Ralph should execute decisions, not discover them halfway through implementation.

## Required Shape

```markdown
# PRD: [Feature Name]

## Introduction
[Current problem and why this work exists.]

## References
- `path/to/relevant/source`
- `path/to/architecture.md`

## Decisions
- [Already-decided constraint.]
- [Old behavior that must not be preserved.]

## Goals
- [Desired outcome.]

## Non-Goals
- [Explicitly out of scope.]

## User Stories

### US-001: [Small task]
**Description:** As a [role], I want [capability] so that [benefit].

**Acceptance Criteria:**
- [ ] [Verifiable result]
- [ ] Typecheck passes
- [ ] Focused tests pass

## Functional Requirements
- FR-1: The system must ...

## Validation
- [Exact command or observable product validation.]

## Risks
- [Known risk and how to detect it.]
```

## Good Decisions

Good decisions reduce agent drift:

- "Do not preserve the old runtime as a fallback."
- "Use schema version 2 and reject schema version 1."
- "Use platform trash, not hard delete."
- "Run real integration validation for success paths."
- "This run does not add a compatibility fallback."
- "This run preserves user data directories during setup, update, and repair."

Weak decisions cause drift:

- "Clean this up."
- "Improve robustness."
- "Make it production ready."
- "Handle edge cases."

## Story Sizing

One story should fit one fresh agent iteration.

Good:

- "Add parser for manifest v2 and tests."
- "Remove deprecated CLI flag from parser and help text."
- "Add status JSON field for new runtime health."

Too large:

- "Migrate the whole runtime."
- "Rewrite onboarding."
- "Make the release process production ready."

Split by dependency order:

1. types and parsers
2. isolated helpers
3. call-site migration
4. CLI/product output
5. tests and validation
6. cleanup guards

## Acceptance Criteria

Use criteria a fresh agent can check:

- "Reject v1 manifests with error code `legacy_manifest_unsupported`."
- "Generated config does not include `runtime.binary`."
- "Run `npm run typecheck`."
- "Run `node --test tests/foo.test.ts`."
- "Verify in browser at `http://localhost:3000/settings`."

Avoid:

- "Works well."
- "Looks good."
- "Handles all cases."
- "No regressions."

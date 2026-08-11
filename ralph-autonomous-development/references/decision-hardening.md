# Decision Hardening Before Ralph

Ralph works best when ambiguity is removed before autonomous execution starts. Use `grill-me` or `grill-with-docs` to turn a vague plan into decisions that can be copied into the PRD.

## Which Grill

Use `grill-me` when:

- the repo has little formal architecture documentation
- the user is still shaping the plan
- the main risk is unclear scope or hidden assumptions

Use `grill-with-docs` when:

- the repo has `CONTEXT.md`, ADRs, architecture docs, or strong domain vocabulary
- the feature must align with existing module ownership
- durable terminology or decisions should be written back to docs

## Prompt Pattern

```text
Use grill-me before writing the Ralph PRD.
Question the plan one decision at a time.
For each question, recommend an answer and explain the tradeoff briefly.
Focus on scope, non-goals, validation, dependencies, rollback, and forbidden shortcuts.
Stop when the decisions are concrete enough to become PRD Decisions and Acceptance Criteria.
```

For doc-heavy repos:

```text
Use grill-with-docs before writing the Ralph PRD.
Challenge the plan against existing architecture docs and domain language.
Surface conflicts with current conventions.
Propose doc updates only for durable accepted decisions.
```

## Questions To Resolve

Ask one question at a time. Prefer exploring the codebase over asking when the answer is discoverable.

Core questions:

- What problem is this run solving, and what user-visible or maintainer-visible outcome proves it?
- What existing behavior must be preserved?
- What old behavior must not be preserved, even as a compatibility fallback?
- Which files or modules are source of truth?
- Which parts of the repo are out of scope?
- What validation proves success beyond unit tests?
- What is allowed to be mocked, and what must be real?
- What is the rollback plan if an iteration breaks a core path?
- What terms must be used consistently in code, docs, and commit messages?
- What would count as a failed Ralph story even if tests pass?

Architecture questions:

- What is the intended dependency direction?
- Which layer owns the public API or protocol?
- Which layer owns persistence/state?
- Which layer owns external process, network, or browser interaction?
- Are migrations required, forbidden, or intentionally deferred?
- Are old entrypoints deleted, deprecated, or preserved?

Execution questions:

- How small should each story be?
- Which stories must come before others?
- What focused test command should each story run?
- What final aggregate validation should close the run?
- What residue guard can prevent forbidden behavior from returning?

## Output Format

End Phase 0 with a compact summary:

```markdown
## Hardened Decisions

- Decision: ...
- Non-goal: ...
- Forbidden shortcut: ...
- Validation gate: ...
- Source of truth: ...
- Risk: ...
- Open question: ...
```

Copy this summary into the PRD's `Decisions`, `Non-Goals`, `Validation`, and `Risks` sections before converting to `prd.json`.


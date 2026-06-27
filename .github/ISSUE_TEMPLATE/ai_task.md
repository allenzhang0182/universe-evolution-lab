---
name: AI Task
about: Standardized task issue for AI executors (OpenHands, SWE-agent, Zoo Code, Aider, etc.)
title: "[AI Task]: <short task title>"
labels: ai-task
assignees: ""
---

> **Important**: This is a **static task template** for human-defined or human-approved AI-assisted tasks.
> It follows the [SOP v2 risk-graded workflow](../../.ai-dev-rules.md).
> AI executors **must** read [`AGENTS.md`](../../AGENTS.md) and [`REVIEW_POLICY.md`](../../REVIEW_POLICY.md) before starting.

---

## Basic Information

| Field             | Value |
|-------------------|-------|
| **Task ID**       | `T-XXX` |
| **Risk Level**    | `readonly` / `low` / `medium` / `high` / `milestone` |
| **Recommended Tool** | (e.g., Zoo Code + DeepSeek, Aider + DeepSeek, Codex + Claude + ChatGPT) |
| **Related Files** | (list of related file paths, one per line) |

---

## Background

### Background

<!-- Provide context: why is this task needed? What problem does it solve? -->

### Goal

<!-- What is the desired outcome? Be specific and measurable. -->

---

## Scope

### Allowed Files

<!-- List files that may be modified. One per line using bullet points. -->

-
-

### Forbidden Files

<!-- List files that must NOT be modified. One per line using bullet points. -->

- `.env`
- production configuration files
- (add more as needed)

---

## Requirements

### Requirements

<!-- Functional and non-functional requirements. -->

-
-

### Acceptance Criteria

<!-- Be specific and testable. Each criterion should be independently verifiable. -->

- [ ]
- [ ]

### Test Commands

```bash
# Command(s) to verify the changes. Example:
# npm test
# npm run lint
# git diff --name-only
```

### Review Requirements

<!-- Specify what needs to be reviewed and by whom. -->

-
-

---

## Stop Conditions

> **AI executors must immediately stop and report if any of the following occur:**

- [ ] A file outside **Allowed Files** needs to be modified
- [ ] A file listed in **Forbidden Files** is touched
- [ ] A new file (not listed in Allowed Files) needs to be created
- [ ] The task involves `.env`, secrets, tokens, or API keys
- [ ] The task involves authentication, permissions, database schema, policy, audit, data deletion, or production deployment (→ **escalate to high** and wait for human confirmation)
- [ ] `git push` is about to be executed (→ **DO NOT push** without explicit human approval)
- [ ] `git merge main` is about to be executed (→ **DO NOT merge** without explicit human approval)

---

## AI Completion Report

> **To be filled by the AI executor after completing the task.**

### Modified Files

| File | Changes Made |
|------|-------------|
| `path/to/file` | (summary of changes) |
| `path/to/file` | (summary of changes) |

### Tests Executed

```bash
# Commands executed
```

### Test Results

- [ ] All tests passed
- [ ] Some tests failed (see below)

<!-- If tests failed, describe which ones and why -->

### Risk Points

<!-- Any remaining risk concerns? -->

### Human Review Required?

- [ ] Yes — explain why
- [ ] No

### Confirmations

- [ ] **No `git commit`** — confirmed no automatic commit was performed
- [ ] **No `git push`** — confirmed no automatic push was performed
- [ ] **No `git merge main`** — confirmed no automatic merge was performed
- [ ] **No forbidden files modified** — confirmed no changes to `.env`, secrets, tokens, or production config

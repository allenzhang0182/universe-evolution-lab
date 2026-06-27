## Description

<!-- Provide a brief summary of the changes in this PR. What does it do and why? -->

Closes #(issue-number)

---

## SOP v2 Review

### Risk Level

<!-- Select the appropriate risk level for this PR. See .ai-dev-rules.md for definitions. -->

- [ ] **readonly** — Read-only analysis, documentation review, code explanation (no code changes)
- [ ] **low** — Bug fix, test update, minor doc change, small config tweak
- [ ] **medium** — Scoped feature, moderate refactor, dependency update without security or schema impact
- [ ] **high** — Authentication, permissions, DB schema, policy, audit, auto-exec commands, production config, data deletion
- [ ] **milestone** — Major release, cross-cutting change, breaking API, security audit

### Scope Control

- [ ] All modified files are within the **Allowed Files** defined in the task
- [ ] No modifications to files listed in **Forbidden Files**
- [ ] No unrelated or scope-creep changes
- [ ] Any new files created are explicitly permitted by the task

### Safety Checks

- [ ] `.env` has **not** been modified
- [ ] No secrets, tokens, or API keys are included in the diff
- [ ] No real production configuration has been modified
- [ ] No automatic `git push` was performed
- [ ] No `git merge main` was performed
- [ ] No destructive commands (`rm -rf`, `git reset --hard`, `git clean -fd`) were executed

### High-Risk Review

<!-- If the risk level is high or milestone, ALL of the following must be checked and reviewed by a human. -->

- [ ] Does this PR involve **authentication**? (login, signup, OAuth, JWT, sessions)
- [ ] Does this PR involve **authorization / permissions**? (RBAC, ACL, access control)
- [ ] Does this PR involve **database schema changes**? (migrations, column changes, indexes)
- [ ] Does this PR involve **policy changes**? (security policy, compliance, terms)
- [ ] Does this PR involve **audit-related changes**? (audit logs, audit trails)
- [ ] Does this PR involve **data deletion**? (DROP, DELETE, TRUNCATE, data purge)
- [ ] Does this PR involve **production deployment**? (deploy scripts, environment config)
- [ ] If **high** or **milestone**: has a human reviewed and approved the changes?

> If any of the above is **Yes**, the risk level must be **high** or **milestone**, and human review is required before merging.

### Test Evidence

<!-- Provide the actual test commands run and their output. -->

**Test commands executed:**

```bash

```

**Test results:**

- [ ] All tests passed
- [ ] Some tests failed (describe below)
- [ ] Tests were not run (explain why)

```
<!-- Paste test output here, or explain why tests were not run -->
```

### AI Tooling

<!-- Document which AI tools were used and whether SOP v2 process files were followed. -->

- **AI tools used**: (e.g., Zoo Code + DeepSeek, Aider + DeepSeek, ChatGPT, Copilot, Codex, Claude, Cursor)
- **`AGENTS.md` read**: Yes / No
- **`REVIEW_POLICY.md` followed**: Yes / No
- **`TASK_QUEUE.md` updated** (if applicable): Yes / No / N/A
- **`.ai-dev-rules.md` followed**: Yes / No

---

## Type of Change

- [ ] 🚀 Feature (non-breaking change)
- [ ] 🐛 Bug fix (non-breaking change)
- [ ] 🔧 Refactor (no functional changes)
- [ ] 📝 Documentation update
- [ ] ⚡ Performance improvement
- [ ] 🛠️ Chore (tooling, dependencies, CI)
- [ ] ⚠️ Breaking change (fix or feature that changes existing behavior)

## How Has This Been Tested?

- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing (describe below)

### Test Steps

<!-- Describe the steps to verify the changes. -->

## Checklist

- [ ] My code follows the project's code style
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing tests pass locally
- [ ] Any dependent changes have been merged and published
- [ ] I have checked for and removed any `console.log` / `debugger` statements
- [ ] I have not included any API keys, secrets, or `.env` files

## Screenshots (if applicable)

<!-- Add screenshots to help explain your changes. -->

## Additional Context

<!-- Add any other context about the PR here. -->

---
name: ship-vertical-slice
description: Implement and ship one bounded vertical feature in this repository. Use when the owner asks for an end-to-end feature, fix, or phase result including tests and Git delivery. Do not use for read-only review or broad product research.
---

# Ship Vertical Slice

1. Verify the repository root, branch, status, remote, and base SHA.
2. Read only the relevant active specification and affected code.
3. Give a short inline plan.
4. Implement concrete code without speculative layers.
5. Add targeted tests for changed behavior.
6. Run targeted checks during work.
7. Run one final `uv sync --frozen`, Ruff, mypy, pytest, and relevant end-to-end smoke.
8. Perform one focused self-review.
9. Run a security diff scan only when the change touches network, secrets, auth, external input,
   filesystem boundaries, database schema/integrity, or destructive behavior.
10. Apply at most one remediation cycle.
11. Create 3–5 logical commits for a large slice, fewer for a small change.
12. Push, open a PR, and merge only when explicitly included in the task.
13. Return a short factual report.

Do not create a separate plan document unless a public contract, schema, or dependency requires it.
Do not repeat completed audits, run deep security scans, create future architecture, commit secrets or
runtime artifacts, force-push, or amend reviewed commits.

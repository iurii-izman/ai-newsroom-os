---
name: focused-review
description: Perform one concise read-only review of a Git diff for merge-blocking correctness and security issues. Use explicitly before merge or when the owner asks to review a change. Do not implement fixes or report style preferences.
---

# Focused Review

1. Verify the exact base and head SHAs.
2. Inspect the changed code and relevant tests.
3. Focus on the normative and public contract, correctness, data integrity, security boundaries,
   secret handling, error handling, and regression risk.
4. Report only Blocker, High, and material Medium findings.
5. Include the file or symbol, failure scenario, and minimal correction for every finding.
6. Ignore style, naming, speculative architecture, and future improvements.
7. Return exactly one verdict: `PASS`, `PASS_WITH_MATERIAL_MEDIUM`, or `FAIL`.

This skill is read-only and does not implement fixes.

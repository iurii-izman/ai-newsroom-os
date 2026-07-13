---
name: f0-scope-guardian
description: Review an F0 implementation plan or Git diff against F0_TECHNICAL_SPEC.md for scope violations. Use only for explicit F0 scope-compliance review; do not use for implementation, automatic fixes, general review, or F1 planning.
---

# F0 Scope Guardian

Review an explicitly supplied F0 implementation plan or the current Git diff without modifying files.

## Review procedure

1. Read `F0_TECHNICAL_SPEC.md` and `AGENTS.md` completely.
2. Read the proposed implementation plan or inspect the current Git diff, as requested.
3. Treat `F0_TECHNICAL_SPEC.md` as the sole normative source. Treat the minimal-scope checklist as derived and historical Foundation or audit documents as non-normative.
4. Map every planned or changed behavior to the F0 whitelist and check every explicit non-goal.
5. Audit project-declared direct dependencies separately from permitted transitive dependencies.
6. Detect and report any introduction or pre-creation of:
   - network access;
   - Docker;
   - UI or API;
   - real LLM providers, provider seams, prompts, retries, or costs;
   - live ingestion or manual URL ingestion;
   - clustering, deduplication, or multi-source merge;
   - TTS, video, publishing, or platform adapters;
   - future placeholder abstractions, entities, modules, tables, or commands;
   - CLI commands outside the exact F0 command set;
   - historical documents used as normative sources.
7. Cite exact file paths and concrete evidence for every violation or warning. For plan-only evidence, cite the relevant plan item.
8. Make no file edits, automatic fixes, commits, or dependency changes.
9. Mark the verdict `FAIL` when any blocking scope violation exists; otherwise mark it `PASS`.

Return exactly these sections:

```markdown
## Verdict
PASS | FAIL

## Blocking violations

## Warnings

## Requirement coverage
```

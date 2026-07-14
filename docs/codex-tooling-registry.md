# Codex Tooling Registry

This registry lists only Codex tools confirmed as installed or enabled during repository bootstrap.

| Tool | Type | Purpose | Permissions posture | Enabled phase | Removal/disable condition |
|---|---|---|---|---|---|
| GitHub | Plugin/App | Repository, PR, issue and CI access | Read-first; external writes require confirmation | Bootstrap/F0+ | Disable when no remote work |
| Codex Security | Plugin | Security scans and diff review | Read/review by default; fixes require explicit task | Post-F0 | Disable outside security tasks |
| Plugin Management | App | Inspect/manage plugin permissions | Administrative | As needed | Keep only while plugin management is useful |
| `ship-vertical-slice` | Repo-local skill | Implement, verify, and optionally ship one bounded feature | Explicit-only | F1+ | Retire when the repository delivery flow changes |
| `focused-review` | Repo-local skill | Review one exact Git diff for material merge blockers | Explicit-only, read-only | F1+ | Retire when the review policy changes |

- Custom MCP servers: none.
- Browser automation: disabled.
- Project runtime network: disabled.
- `.env` is ignored local configuration, not a tool or tracked artifact; only `.env.example` is
  tracked and it contains an empty credential placeholder.

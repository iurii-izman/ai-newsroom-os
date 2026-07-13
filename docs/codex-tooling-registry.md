# Codex Tooling Registry

This registry lists only Codex tools confirmed as installed or enabled during repository bootstrap.

| Tool | Type | Purpose | Permissions posture | Enabled phase | Removal/disable condition |
|---|---|---|---|---|---|
| GitHub | Plugin/App | Repository, PR, issue and CI access | Read-first; external writes require confirmation | Bootstrap/F0+ | Disable when no remote work |
| Codex Security | Plugin | Security scans and diff review | Read/review by default; fixes require explicit task | Post-F0 | Disable outside security tasks |
| Plugin Management | App | Inspect/manage plugin permissions | Administrative | As needed | Keep only while plugin management is useful |

- Custom MCP servers: none.
- Browser automation: disabled.
- Project runtime network: disabled.

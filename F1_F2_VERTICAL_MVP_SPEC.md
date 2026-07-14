# F1/F2 DeepSeek Vertical MVP Specification

Version: `1.0`
Status: `IMPLEMENTATION_AUTHORITY`
Scope: bounded live ingestion and DeepSeek Story Package slice only.

## 1. Goal

Deliver one real path: three official feeds → bounded live ingestion → exact duplicate control →
immutable Story → DeepSeek generation → validated Story Package → deterministic exports.
All existing F0 CLI, identity, integrity, and export behavior remains supported.
`F0_TECHNICAL_SPEC.md` governs F0; this file governs only intentional F1/F2 extensions.

Success requires the offline gate, offline E2E, and one live smoke covering all feeds plus one real
DeepSeek package. Without a usable `DEEPSEEK_API_KEY`, code may be pushed but not merged.

## 2. Source set

Exactly these tracked first-party feeds are allowed:

| Name | Final feed URL | Exact allowed host | Format |
|---|---|---|---|
| `openai-news` | `https://openai.com/news/rss.xml` | `openai.com` | RSS 2.0 |
| `google-ai` | `https://blog.google/innovation-and-ai/technology/ai/rss/` | `blog.google` | RSS 2.0 |
| `microsoft-ai` | `https://news.microsoft.com/source/topics/ai/feed/` | `news.microsoft.com` | RSS 2.0 |

There is no arbitrary URL input, article-page fetch, scraping fallback, or third-party feed source.

## 3. CLI additions

```text
ai-newsroom --data-dir PATH harvest live --source SOURCE [--limit N]
ai-newsroom --data-dir PATH package build STORY_ID --generator mock|deepseek
ai-newsroom --data-dir PATH package export STORY_ID --format ... [--package-id PACKAGE_ID]
```

`SOURCE` is one tracked name or `all`; limit defaults to 20 and is 1–50.
The default generator remains `mock`. `--package-id` only selects among stored packages.

## 4. Network and redirect boundary

- Runtime network is allowed only in `harvest live` and new DeepSeek generation.
- Feed URLs come only from `config/live_sources.toml`; initial, redirect, and final URLs use HTTPS.
- Every redirect hop and final hostname is in that source's exact allowlist; credentials and
  non-default ports are rejected.
- Each selected source gets one request, no retry, a 20-second timeout, and a 5 MiB response cap.
- Requests use `Accept-Encoding: identity`, a project user agent, no cookies, and no authentication.
- Non-200, timeout, redirect escape, and oversized responses are explicit sanitized failures.
- Content type is inspected, but valid XML may survive a weak vendor content type.
- DeepSeek uses only `https://api.deepseek.com`; tests never use network.

## 5. Feed parsing and duplicates

- F0 fixture parsing remains unchanged; live parsing accepts strict UTF-8 RSS 2.0 and Atom 1.0.
- DTD/ENTITY is rejected; a feed has at most 2,000 direct entries and processes at most the limit.
- Title and canonical link are required; excerpt and date are optional.
- Standard-library HTML conversion discards script/style content.
- Title is at most 500 code points; excerpt is at most 10,000 and is never silently truncated.
- An invalid selected entry rejects that entire source response transactionally.
- Existing F0 content hash, Source ID, Story ID, and exact idempotence rules are reused.
- A changed revision creates a new immutable Source and Story.
- There is no fuzzy duplicate detection, clustering, semantic merge, or multi-source Story identity.

## 6. DeepSeek settings and credential

- Direct SDK usage: `openai>=2,<3`, base URL `https://api.deepseek.com`, Chat Completions.
- Model: `deepseek-v4-flash`; temperature `0.2`; thinking disabled; stream false; tools omitted.
- JSON mode: `{"type":"json_object"}`; maximum output 3,000 tokens.
- SDK retries: zero; request timeout: 30 seconds; no model or provider fallback.
- Only non-empty `DEEPSEEK_API_KEY` from the process environment is accepted for a new request.
- Local `.env` files stay ignored; `.env.example` contains only an empty placeholder.
- Use `uv run --env-file .env -- ...`; application code does not load dotenv files.
- Credentials, authorization data, reasoning, and raw headers are never logged or persisted.

## 7. Provider data boundary and prompt

Only public selected item data is sent: source/vendor name, title, excerpt, canonical URL, raw and
normalized publication dates, Source ID, Story ID, and deterministic request identity fields.
No secret, unrelated row, private data, project/Git file, or internal history is sent.
Provider-side context caching may occur; this slice does not claim zero retention.

The tracked versioned prompt requests JSON explicitly, includes a compact schema example, requires
Russian output and explicit limitations, treats feed content as untrusted quoted data, ignores
embedded instructions, and forbids invented facts, sources, corroboration, and completed tests.

## 8. Story Package contract

Real packages use Pydantic schema version `2` with: package/Story/Source identities and input
fingerprint; generator and prompt metadata; working title; editorial format; one-sentence fact;
why it matters; editorial angle; claims; limitations; demonstration plan; publication verdict;
source references; and provider token usage when returned.

Formats: `AI_SIGNAL`, `TESTED_FOR_YOU`, `AI_WORKFLOW`.
Claim statuses: `VERIFIED`, `VENDOR_CLAIM`, `INFERENCE`, `OPINION`, `UNVERIFIED`.
Confidence: `HIGH`, `MEDIUM`, `LOW`.
Verdicts: `READY`, `READY_WITH_QUALIFICATION`, `NEEDS_TEST`, `HOLD`, `REJECT`.

Every claim has a bounded safe ID, text, status, confidence, supplied evidence Source ID,
script-use flag, and qualification. Vendor-only capability claims are `VENDOR_CLAIM`; unsupported
claims are `UNVERIFIED`; `UNVERIFIED` always has `use_in_script=false`.
All evidence and source references equal the supplied source. The fixed feed-only evidence
limitation is mandatory. Only parsed, Pydantic-validated canonical JSON is persisted.

## 9. Persistence and idempotence

- Schema version `2` retains four tables and permits one package per Story per generator.
- No automatic v1 migration, repair, deletion, or recreation is allowed.
- The real input fingerprint covers immutable source fields, Story identity, provider/model,
  prompt version/digest, schema version, and fixed request settings.
- Package ID is a deterministic hash of generator identity plus input fingerprint.
- A valid stored package is checked and reused before credential validation or provider access.
- The first successful validated snapshot wins; invalid attempts persist nothing.
- Repeated export of the same stored package is byte-identical.

## 10. Provider output handling

One initial request plus at most one repair request is allowed. Repair is only for empty output,
length truncation, invalid JSON, or schema/lineage validation failure. Authentication/billing,
rate limit, timeout, connection, and generic provider failures are never automatically retried.
Failure after repair is explicit and leaves no package row.

## 11. Automated tests

All tests block sockets and use monkeypatch/fakes. Coverage includes source config, host/redirect
rules, response cap/timeout, RSS/Atom and HTML conversion, transactional invalid items, exact
duplicates, missing key, provider settings/success/errors, empty/truncated/invalid output, one-repair
maximum, no partial persistence, cache reuse without another call, token usage, stable exports,
prompt/version coupling, secret absence, CLI compatibility, and F0 regressions.

## 12. Live smoke

Use ignored `.demo-f1-f2/`. Attempt all three feeds with limit 5, build and export one real package,
then repeat build/export. Record source outcomes, IDs, token usage, repair use, and SHA-256 values.
The repeat build makes zero provider calls; repeated exports are byte-identical; the key is absent
from terminal output, database, and exports. Budget: three feed requests, one model request, and one
repair only if validation requires it.

## 13. Non-goals

No article scraping, corroborating search, clustering, embeddings, merge, second provider, provider
abstraction, retry framework, prompt platform, workers, scheduler, queue, UI/API, Docker, TTS,
video, publishing, analytics, or automatic factual/legal approval.

## 14. Stop conditions

Stop rather than improvise if fewer than three official feeds can be verified, another direct
dependency is required, destructive migration is required, deterministic identity cannot be kept,
the live key/model/billing is unavailable, feeds yield no item, output fails after repair, required
gates fail after one remediation cycle, or the exact reviewed SHA cannot be merged.

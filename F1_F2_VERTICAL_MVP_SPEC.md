# F1/F2 DeepSeek Vertical MVP Specification

Version: `1.0`
Status: `IMPLEMENTATION_AUTHORITY`
Scope: the bounded live-ingestion and DeepSeek Story Package slice only.

## 1. Objective

Deliver one real vertical path:

```text
three official feeds
→ bounded live ingestion
→ exact duplicate control
→ immutable Story
→ one DeepSeek call path
→ validated Story Package
→ deterministic exports
```

All existing F0 CLI behavior and identity rules remain supported.
`F0_TECHNICAL_SPEC.md` remains authoritative for F0 behavior.
This file is authoritative only where this slice intentionally extends F0.

## 2. Success criterion

Success requires all offline checks plus one live smoke with all three feeds and one DeepSeek package.
The live smoke must prove stored-package reuse and byte-identical repeated exports.
If `DEEPSEEK_API_KEY` is absent, implementation and offline evidence may finish and the branch may be
pushed, but no PR or merge is allowed.

## 3. Source set

Exactly these tracked sources are allowed:

| Name | Final feed URL | Allowed hosts | Format |
|---|---|---|---|
| `openai-news` | `https://openai.com/news/rss.xml` | `openai.com` | RSS 2.0 |
| `google-ai` | `https://blog.google/innovation-and-ai/technology/ai/rss/` | `blog.google` | RSS 2.0 |
| `microsoft-ai` | `https://news.microsoft.com/source/topics/ai/feed/` | `news.microsoft.com` | RSS 2.0 |

The URLs were linked by first-party pages and returned HTTP 200 XML during discovery.
There is no arbitrary URL input or HTML scraping fallback.

## 4. Network and redirect boundary

- Runtime network is allowed only for `harvest live` and DeepSeek generation.
- Feed URLs come only from `config/live_sources.toml`.
- Initial and redirect URLs must use HTTPS.
- Every redirect hop and final hostname must be in that source's exact allowlist.
- Feed timeout is at most 20 seconds.
- Feed response size is at most 5 MiB.
- Requests use `Accept-Encoding: identity` and a project user agent.
- Requests use no cookies, authentication, or application proxy configuration.
- One initial fetch is made per selected source; there are no retries.
- Non-200, timeout, redirect escape, and oversized responses are explicit failures.
- Content type is inspected, but valid XML survives a weak vendor content type.
- Article pages are never fetched.

## 5. Feed parsing behavior

- F0 fixture parsing remains its exact RSS 2.0 subset.
- Live parsing accepts RSS 2.0 and Atom 1.0.
- A live document is strict UTF-8, rejects DTD/ENTITY, and is bounded before parsing.
- A live document contains at most 2,000 direct entries; at most the requested 1–50 are processed.
- Required fields are title and canonical link.
- Summary/content and publication date are optional.
- HTML is converted to plain text with the standard library.
- Script and style content is discarded.
- Normalized title remains at most 500 code points.
- Normalized excerpt remains at most 10,000 code points and is never silently truncated.
- Source name, title, link, excerpt, raw date, and normalized date are mapped.
- Invalid selected entries transactionally reject that entire source response.
- No invalid selected entry is silently skipped.

## 6. Duplicate policy

The F0 normalized content hash, source ID, and Story ID rules remain unchanged.
Repeated normalized input creates no new Source or Story rows.
A changed source revision creates a new immutable Source and Story.
There is no fuzzy matching, semantic clustering, or cross-source merge.

## 7. CLI additions

```text
ai-newsroom --data-dir PATH harvest live --source SOURCE [--limit N]
ai-newsroom --data-dir PATH package build STORY_ID --generator mock|deepseek
ai-newsroom --data-dir PATH package export STORY_ID --format ... [--package-id PACKAGE_ID]
```

`SOURCE` is one tracked name or `all`.
The default limit is 20 and valid range is 1–50.
The default generator remains `mock`.
`--package-id` is only a selector when a Story has multiple stored packages.

## 8. DeepSeek API settings

- Client: direct `openai>=2,<3` SDK usage.
- Base URL: `https://api.deepseek.com`.
- Endpoint: `/chat/completions`.
- Model: `deepseek-v4-flash` only.
- Temperature: `0.2`.
- Thinking: disabled.
- Stream: false.
- Tools: omitted.
- Response format: `{"type":"json_object"}`.
- Maximum output tokens: 3,000.
- SDK automatic retries: zero.
- Request timeout: 30 seconds.
- Credential: non-empty `DEEPSEEK_API_KEY` from the current process only.

## 9. Data boundary and caching limitation

Only public data for one Story is sent: normalized title and excerpt, canonical URL, raw and normalized
publication dates, source name, source ID, Story ID, and deterministic package identity metadata.
No project file, unrelated row, user data, secret, environment value, Git data, or internal history is
sent. The tracked runtime prompt is the only instruction asset.
DeepSeek may perform provider-side context caching.
This slice does not claim zero retention.
Private or licensed internal content is outside the approved boundary.

## 10. Story Package schema

Real packages use schema version `2` and contain:

```text
schema_version, package_id, story_id, source_id, input_fingerprint,
generator, prompt_version, working_title, editorial_format,
one_sentence_fact, why_it_matters, editorial_angle, claims,
limitations, demonstration_plan, publication_verdict,
source_references, usage_metadata
```

Formats are `AI_SIGNAL`, `TESTED_FOR_YOU`, and `AI_WORKFLOW`.
Claim statuses are `VERIFIED`, `VENDOR_CLAIM`, `INFERENCE`, `OPINION`, and `UNVERIFIED`.
Confidence is `HIGH`, `MEDIUM`, or `LOW`.
Verdicts are `READY`, `READY_WITH_QUALIFICATION`, `NEEDS_TEST`, `HOLD`, or `REJECT`.
Every claim has ID, text, status, confidence, evidence source ID, script-use flag, and qualification.
`UNVERIFIED` always means `use_in_script=false`.
All evidence IDs and source references must equal the supplied source.
The fixed feed-only evidence limitation is mandatory.
Provider token usage is stored when reported; price is not calculated.
No reasoning, key, authorization header, or raw request header is stored.

## 11. Identity, persistence, and idempotence

The real input fingerprint covers immutable source fields, Story identity, provider, model, prompt
version and digest, package schema version, and fixed request settings.
The real package ID is a stable hash of generator identity plus input fingerprint.
The package ID is checked before any provider request.
A valid existing package is returned without another provider call.
The first successful validated snapshot wins.
Invalid attempts leave no package row.
Repeated export of one stored package is byte-identical.

The four-table layout is retained, but schema version `2` is required because F0 schema v1 permits
only `mock` and only one package per Story. Schema v2 permits one package per Story per generator.
There is no automatic v1 migration, repair, deletion, or recreation.
An existing incompatible database is refused; F0 data remains disposable.

## 12. Error behavior

Expected CLI errors are concise, sanitized, non-zero, and traceback-free.
Missing credential, authentication/billing, rate limit, timeout, server failure, empty output,
truncation, invalid JSON, and schema failure remain distinct conditions.
SDK retries and provider/model fallback are forbidden.
Empty, length-truncated, invalid-JSON, or schema-invalid output permits one repair call.
No other failure permits repair or retry.
The repair uses identical model/settings and public source input plus a concise validation summary.
At most two model calls occur for one new package.

## 13. Offline tests

All automated tests block sockets.
Injected responses cover source configuration, host/redirect rules, response cap, timeout, RSS, Atom,
HTML conversion, transactional item failure, duplicate harvest, DeepSeek success, empty/truncated/
invalid output, repair success/failure, provider errors, usage, idempotence, stable exports, CLI surface,
prompt version coupling, F0 regressions, and secret absence.
No pytest test calls a real feed or DeepSeek.

## 14. Live smoke

Use ignored `.demo-f1-f2/` only.
Attempt all three feeds with limit 5.
Build one DeepSeek package and export JSON plus Markdown.
Repeat build and export for the same package.
Record source outcomes, IDs, token usage, repair use, and file SHA-256 values.
The second build must make zero provider calls.
The credential must be absent from terminal output, database, and exports.

## 15. Non-goals

No article scraping, corroborating-source search, clustering, embeddings, merge, second provider,
provider abstraction, prompt platform, retries framework, workers, scheduler, queue, UI, API, Docker,
TTS, video, publishing, analytics, or automatic factual/legal approval is included.

## 16. Stop conditions

Stop rather than improvise when a source cannot be verified, another direct dependency is required,
a destructive migration is required, deterministic identity cannot be maintained, the live key/model/
billing is unavailable, feeds yield no item, output fails after repair, required gates fail after the
single remediation allowance, or the exact reviewed SHA cannot be merged.

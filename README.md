# AI Newsroom OS

AI Newsroom OS is a proof-first automation system for a Russian-speaking AI newsroom. It preserves
traceable relationships between sources, claims, editorial conclusions, and practical applications
without treating vendor feed content as independently verified truth.

**Status:** F0 through F3 are implemented. The first local vertical MP4 was generated successfully
and remains in ignored `.demo-video/` pending manual approval; nothing is published automatically.

## Document authority

1. [`F0_TECHNICAL_SPEC.md`](F0_TECHNICAL_SPEC.md) remains the sole normative specification for F0.
2. [`F1_F2_VERTICAL_MVP_SPEC.md`](F1_F2_VERTICAL_MVP_SPEC.md) governs only the live-ingestion and
   DeepSeek vertical slice.
3. [`F3_SCRIPT_VIDEO_MVP_SPEC.md`](F3_SCRIPT_VIDEO_MVP_SPEC.md) governs only the script and video
   pilot slice.
4. [`PROJECT_VISION.md`](PROJECT_VISION.md) is non-normative product context.

Historical prompts, audits, plans, and reports are retained evidence only and never override the
root phase specifications or [`AGENTS.md`](AGENTS.md).

## Local setup

```powershell
uv sync --frozen
Copy-Item .env.example .env
```

Put the local `DEEPSEEK_API_KEY` in `.env` when using the real generator. Never commit `.env` or
another file containing the key. The application reads the process environment directly; `uv`
loads the local file for an explicitly opted-in command, while an existing environment value takes
precedence.

## Commands

Existing F0 commands remain valid. The vertical slice adds:

```powershell
uv run --env-file .env -- ai-newsroom --data-dir data harvest live --source openai-news --limit 20
uv run --env-file .env -- ai-newsroom --data-dir data harvest live --source all --limit 5
uv run --env-file .env -- ai-newsroom --data-dir data package build STORY_ID --generator deepseek
uv run --env-file .env -- ai-newsroom --data-dir data package export STORY_ID --format all --package-id PACKAGE_ID
uv run --env-file .env -- ai-newsroom --data-dir data script build STORY_ID --package-id PACKAGE_ID
uv run -- ai-newsroom video render SCRIPT_JSON
```

`harvest live` accepts only the three tracked first-party sources. The default package generator is
still `mock`, so the old F0 invocation remains unchanged.

## DeepSeek provider boundary

The concrete provider is DeepSeek at `https://api.deepseek.com/chat/completions`, using
`deepseek-v4-flash`, JSON Output, temperature `0.2`, disabled thinking, no tools, no streaming, and
at most one schema-repair request. Set only `DEEPSEEK_API_KEY` in the current process environment or
load the ignored local `.env` with `uv run --env-file .env -- ...`.

Only public, bounded, feed-derived content for the selected Story may be sent: title, excerpt,
canonical URL, dates, vendor name, source ID, and Story ID. Do not use this slice for private or
licensed internal content. Provider-side context caching may occur; the system does not claim zero
retention. Automated tests remain entirely network-free.

`script build` accepts only a validated stored DeepSeek package and deterministically exports an
editable canonical JSON/Markdown pair with `safe-local-v1`; no script provider is called. Allowed
claims, qualifications, limitations, sources, counts, and identity are finalized locally.
`video render` validates that JSON,
queries the current Edge Russian voice list,
sends only `spoken_text` to Edge TTS, and creates local ignored MP3, SRT, text-card PNG, MP4, and
manifest artifacts. Every script and video remains subject to manual approval before publication.

## Target environment

- Windows 11 and Python 3.12.x
- `uv`, 16 GB RAM, CPU-only
- no Docker or GPU requirement

The manual content-validation track continues independently of this technical slice.

# AI Newsroom OS

AI Newsroom OS is a proof-first automation system for a Russian-speaking AI newsroom. It preserves
traceable relationships between sources, claims, editorial conclusions, and practical applications
without treating vendor feed content as independently verified truth.

**Status:** F1/F2 DeepSeek vertical MVP implemented. Foundation F0 behavior remains supported.

## Document authority

1. [`F0_TECHNICAL_SPEC.md`](F0_TECHNICAL_SPEC.md) remains the sole normative specification for F0.
2. [`F1_F2_VERTICAL_MVP_SPEC.md`](F1_F2_VERTICAL_MVP_SPEC.md) governs only the live-ingestion and
   DeepSeek vertical slice.
3. [`PROJECT_VISION.md`](PROJECT_VISION.md) is non-normative product context.

## Commands

Existing F0 commands remain valid. The vertical slice adds:

```powershell
uv run ai-newsroom --data-dir data harvest live --source openai-news --limit 20
uv run ai-newsroom --data-dir data harvest live --source all --limit 5
uv run ai-newsroom --data-dir data package build STORY_ID --generator deepseek
uv run ai-newsroom --data-dir data package export STORY_ID --format all --package-id PACKAGE_ID
```

`harvest live` accepts only the three tracked first-party sources. The default package generator is
still `mock`, so the old F0 invocation remains unchanged.

## DeepSeek provider boundary

The concrete provider is DeepSeek at `https://api.deepseek.com/chat/completions`, using
`deepseek-v4-flash`, JSON Output, temperature `0.2`, disabled thinking, no tools, no streaming, and
at most one schema-repair request. Set only `DEEPSEEK_API_KEY` in the current process environment.

Only public, bounded, feed-derived content for the selected Story may be sent: title, excerpt,
canonical URL, dates, vendor name, source ID, and Story ID. Do not use this slice for private or
licensed internal content. Provider-side context caching may occur; the system does not claim zero
retention. Automated tests remain entirely network-free.

## Target environment

- Windows 11 and Python 3.12.x
- `uv`, 16 GB RAM, CPU-only
- no Docker or GPU requirement

The manual content-validation track continues independently of this technical slice.

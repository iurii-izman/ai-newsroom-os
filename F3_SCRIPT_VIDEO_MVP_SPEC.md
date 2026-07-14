# F3 Script and Vertical Video MVP Specification

Version: `1.0`
Status: `COMPLETED_MAINTENANCE_AUTHORITY`
Scope: first production script and first local vertical MP4 only.

## 1. Goal and authority

F3 delivers one validated DeepSeek Story Package → Russian script → Russian neural voice →
`TEXT_CARD_V1` → playable MP4 path. `F0_TECHNICAL_SPEC.md` and
`F1_F2_VERTICAL_MVP_SPEC.md` continue to govern their existing behavior.

The pilot is local and requires manual approval. It does not publish content or claim factual,
editorial, or production approval automatically.

## 2. Scope

One run produces a canonical script JSON, editable Markdown, MP3 voice track, SRT subtitles,
cover PNG, scene PNGs, MP4, and manifest with lineage and SHA-256 hashes.

F3 has one script schema, one Edge TTS integration, and one original text-card template. It has no
stock media, third-party footage, music, avatars, logos, analytics, publishing, queues, workers,
web UI, provider abstraction, generic artifact repository, or database migration.

## 3. Dependencies and network

Approved direct runtime additions are `edge-tts>=7.2,<8`, `Pillow>=12.3,<13`, and
`imageio-ffmpeg>=0.6,<1`. Edge provides current Russian voices and timing, Pillow renders original
cards, and imageio-ffmpeg supplies the local FFmpeg executable.

Automated tests are offline. Runtime network is permitted only when the user explicitly invokes
`video render` for Edge TTS, or invokes previously approved F1/F2 network commands.

## 4. Public CLI

```text
ai-newsroom --data-dir PATH script build STORY_ID --package-id PACKAGE_ID [--output-dir PATH]
ai-newsroom video render SCRIPT_JSON [--output-dir PATH] [--voice VOICE]
```

`script build` accepts only a validated stored schema-v2 DeepSeek package. Its first-pilot script
generator is `safe-local-v1`; it performs no provider request. Default script output is
`<data-dir>/scripts/<story-id>/`. `video render` accepts only a canonical F3 script JSON; default
output is a sibling `video/` directory. Expected failures are concise project errors without a
traceback. Existing commands remain compatible.

## 5. Package eligibility and script safety

Mock packages and verdicts `HOLD` or `REJECT` are rejected. `NEEDS_TEST` is eligible only when the
narration explicitly states that the capability remains untested. `READY_WITH_QUALIFICATION`
requires a package qualification in narration.

The Story Package is generated and validated upstream with DeepSeek. The first production script
is then assembled deterministically from claims with `use_in_script=true`, their exact
qualifications, package limitations, source references, and tracked neutral transitions.
`UNVERIFIED` claims and unrelated package fields never enter script narration. No script provider
request is made.

`VENDOR_CLAIM` stays qualified, `INFERENCE` is interpretation, and `OPINION` is editorial. The
feed-only evidence limitation remains present. Output always requires manual approval.

## 6. Script contract and identity

Schema version is `1`; language is `ru`; manual approval is `true`; target duration is 45–75
seconds. The strict model includes script/story/package identity, input fingerprint,
`generator=safe-local-v1`, template version `claim-safe-script-v1`, title, hook, spoken text, word
count, 5–8 scenes with claim IDs, inherited source references, limitations, caption, and approval
flag. The normal target is 110–170 words; a safe first pilot may use 90–109 words rather than add or
repeat claims.

Local code chooses the first `VERIFIED` claim, otherwise the first `VENDOR_CLAIM`, otherwise the
first allowed claim for the hook. It assembles all factual narration from allowed claim text and
qualifications, adds status-compatible evidence language, retains limitations, assigns order and
source labels, and sets `visual_kind=TEXT_CARD`. The final scene is neutral practical advice.

The fingerprint covers the canonical validated package JSON digest, package ID, script schema
version, generator version, and exact template version. `script_id` is derived from that
fingerprint. A stored valid pair with the same identity is reused byte-for-byte before construction.
Free-form script input, prompt v1/v2 execution, and repair calls are not part of this path.

## 7. Script persistence

`<script-id>.json` is sorted, indented canonical UTF-8 with one trailing newline and exactly the
validated model. `<script-id>.md` contains title, hook, narration, scene table, sources,
limitations, and the manual-approval notice.

The pair is written atomically. Identical files are a no-op. A partial pair or differing existing
content is an explicit conflict; files are never silently overwritten. No script/video table is
created. Live snapshots stay ignored.

## 8. TTS

The renderer queries the current voice list once. It chooses `ru-RU-DmitryNeural`, then
`ru-RU-SvetlanaNeural`, then the first `ru-RU` neural voice, or returns `E_TTS_VOICE`. An explicit
voice must also be a current Russian neural voice.

Prosody is rate `+5%`, volume `+0%`, pitch `+0Hz`. Only `spoken_text` is sent. No package metadata,
URL, secret, or unrelated file crosses the TTS boundary. Timing from Edge is retained in SRT.
Failure leaves script files intact, creates no fake MP4, and publishes no success manifest.

## 9. Visuals and encoding

`TEXT_CARD_V1` renders 1080×1920 original dark cards with high-contrast Cyrillic text, a modest
accent, source label, scene counter/progress, and generous margins. It uses Segoe UI, Arial, or
another installed Cyrillic-capable system font; font files are never committed.

Wrapping is deterministic and bounded. Content that cannot fit fails explicitly. The renderer
creates `cover.png` and `scene-01.png` through `scene-N.png`; no third-party visual asset is used.

FFmpeg comes from `imageio_ffmpeg.get_ffmpeg_exe()` and is invoked with subprocess argument lists,
never shell interpolation. A temporary FFconcat file names only generated local scene files.
Durations follow TTS timing when available and otherwise use proportional narration length.

MP4 is H.264/AAC, `yuv420p`, 1080×1920, 30 fps, `-shortest`, and fast-start enabled. The preferred
first-pilot duration is 35–65 seconds; 25–85 seconds is accepted for the approved 94-word script.

## 10. Manifest and verification

The manifest records schema version, script/package/story IDs, template, voice, dimensions, frame
rate, measured duration, creation time, manual approval, artifact paths, and SHA-256 hashes.
Operational creation time does not affect package or script identity.

After encoding, FFmpeg must decode the output and confirm non-empty video and audio streams,
1080×1920 dimensions, and an accepted duration. Render success is reported only after verification.

## 11. Tests and delivery

Offline tests cover package/verdict safety, deterministic claim and qualification retention, no
partial output, stored reuse, stable exports, invalid script rejection, Cyrillic layout, and a
short local WAV-to-MP4 render with video and audio. Existing F0/F1/F2 tests remain green.

The one final gate is `uv sync --frozen`, Ruff, mypy, and pytest. One real ignored pilot smoke then
builds and inspects the script and renders the video. A focused review checks approved dependencies,
claim/TTS boundaries, path and command safety, FFmpeg invocation, ignored media/secrets, and
regression preservation before exact-HEAD PR merge. Manual approval remains mandatory; optional
LLM script polishing is deferred until after the first published pilot.

## 12. Output policy

`.demo-video/` is ignored. Generated live JSON/Markdown snapshots, MP3, SRT, PNG, MP4, manifests,
and FFconcat files are not committed. Code, this specification, prompt, README, and small synthetic
test fixtures may be tracked. The successful pilot output remains local for manual review.

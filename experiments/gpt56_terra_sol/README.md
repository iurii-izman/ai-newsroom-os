# GPT-5.6 Terra vs Sol — controlled Track A evaluation

## Purpose and editorial question

This package prepares one reproducible, small controlled comparison: on one realistic synthetic
Russian CRM integration incident, does GPT-5.6 Sol or GPT-5.6 Terra produce a more accurate and
usable analyst response with fewer critical errors and less manual correction within 20 minutes?

It is not a statistically powered benchmark, a production phase, a universal model ranking, or
publication approval. It does not automate scoring, run six paid calls in a batch, capture hidden
reasoning, estimate labor cost, edit video, or control OBS Studio or CapCut Desktop.

## Design and boundaries

- Six independent valid runs: three Terra and three Sol, in frozen order.
- Preferred mode: OpenAI Responses API, one explicitly confirmed paid call per invocation.
- Fallback mode: manual ChatGPT Work execution and validated local import.
- Blind A–F review uses the tracked rubric; humans enter scores and correction timers.
- Only `01_incident_brief.md`, `02_event_log.csv`, `03_acceptance_criteria.md`, and
  `master_prompt.md` may enter a model request.
- `04_reference_key_NOT_FOR_MODELS.md` is private reviewer material and is never request input.
- All fixtures are synthetic and contain no client data. API data handling is governed by the
  owner's OpenAI agreement and settings; `store=false` prevents later Responses API retrieval but
  this package does not claim zero retention.
- The owner configures credentials, billing limits, account access, OBS recording, ChatGPT Work,
  human review, CapCut assembly, final QA, and publication decisions.

## Official OpenAI contract verification

Verified on **2026-07-16** against official OpenAI sources:

- Model IDs: `gpt-5.6-terra` and `gpt-5.6-sol`.
- Standard text prices per 1M tokens: Terra $2.50 input / $15 output; Sol $5 input / $30 output.
- Both models support Responses API and explicit reasoning effort; this experiment freezes
  `medium` for both.
- Requests use `client.responses.create(model=..., input=..., reasoning={"effort": "medium"},
  max_output_tokens=..., tools=[], tool_choice="none", store=False)`.
- The Python SDK exposes visible `response.output_text`; usage exposes `input_tokens`,
  `output_tokens`, cached-input detail, reasoning-token detail, and total tokens.
- The SDK disables automatic retries with `OpenAI(max_retries=0, timeout=...)`.
- GPT-5.6 is generally available through the API, but actual organization/model access and
  billing remain owner-specific and must be checked manually.

Official sources:

- https://developers.openai.com/api/docs/models/gpt-5.6-terra
- https://developers.openai.com/api/docs/models/gpt-5.6-sol
- https://developers.openai.com/api/reference/resources/responses/methods/create
- https://developers.openai.com/api/docs/guides/reasoning
- https://developers.openai.com/api/docs/guides/conversation-state
- https://developers.openai.com/api/docs/guides/text
- https://github.com/openai/openai-python
- https://openai.com/api/pricing/

Rates and IDs remain configuration values. Cached-input and other pricing categories are recorded
as unavailable by this harness and are not inferred. Long-context, priority, batch, cache-write,
regional, and other pricing variants are outside this bounded fixture.

## Commands

```powershell
uv run python -m ai_newsroom.experiments.gpt56_eval prepare `
  --config experiments/gpt56_terra_sol/config.example.toml `
  --run-root .track-a/gpt56-terra-sol

uv run python -m ai_newsroom.experiments.gpt56_eval status `
  --run-root .track-a/gpt56-terra-sol

uv run python -m ai_newsroom.experiments.gpt56_eval request-preview `
  --run-root .track-a/gpt56-terra-sol --run-id run_01

uv run --env-file .env -- python -m ai_newsroom.experiments.gpt56_eval access-check `
  --run-root .track-a/gpt56-terra-sol --confirm-live --confirm-cost

uv run --env-file .env -- python -m ai_newsroom.experiments.gpt56_eval run-next `
  --run-root .track-a/gpt56-terra-sol --confirm-live --confirm-cost

uv run python -m ai_newsroom.experiments.gpt56_eval blind `
  --run-root .track-a/gpt56-terra-sol

uv run python -m ai_newsroom.experiments.gpt56_eval validate-human-input `
  --run-root .track-a/gpt56-terra-sol

uv run python -m ai_newsroom.experiments.gpt56_eval analyze `
  --run-root .track-a/gpt56-terra-sol

uv run python -m ai_newsroom.experiments.gpt56_eval evidence-manifest `
  --run-root .track-a/gpt56-terra-sol
```

For API execution, set `OPENAI_API_KEY`, a billing/spending limit, and
`AI_NEWSROOM_ALLOW_OPENAI_SMOKE=1` locally. `access-check` uses a neutral minimal prompt and may
incur a small cost. `run-next` executes only the next frozen slot; invoke it six times manually
while recording. Use `--show-output` only when the owner intentionally wants visible terminal
capture.

For ChatGPT Work, set `mode = "chatgpt-work"`, prepare the workspace, execute the frozen slot with
the request preview/input package, then use `import-run` with the exact frozen model ID and effort.
Subscription execution has no measured direct API cost and the harness never fabricates one.

Runtime data lives under `.track-a/gpt56-terra-sol/` and is ignored. Stop on fixture/hash mismatch,
workspace conflict, secret exposure risk, live cost-guard failure, a second invalid replacement,
failed blinding, or invalid human input. Do not continue after identity-bearing configuration or
fixture changes once a valid raw run exists.

## Results and manual evidence

The deterministic analysis reports medians and ranges for three outputs per model, critical
errors, correction time, acceptance within 20 minutes, latency, and API token/cost fields when
available. One synthetic task and six runs cannot establish general model superiority. Close or
contradictory evidence is `MIXED`; integrity failure is `INCONCLUSIVE`.

Record each run manually with OBS after completing the tooling smoke checklist. After analysis,
use the CapCut assembly checklist to build a 60–70 second evidence-first vertical video. Model
identity stays hidden until the result scene. Nothing may be published before owner QA and explicit
approval.

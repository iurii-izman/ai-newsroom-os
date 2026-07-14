from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Final

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    OpenAI,
    RateLimitError,
)

from ai_newsroom.models import F0Error

BASE_URL: Final = "https://api.deepseek.com"
MODEL: Final = "deepseek-v4-flash"
PROMPT_VERSION: Final = "f1f2-story-package-v1"
PROMPT_SHA256: Final = "30df0337c5fed5f96432668d1b23bf7eaaff9112da5b6d05c468e52ab296a31e"
PROMPT_PATH: Final = Path(__file__).resolve().parents[2] / "prompts" / "story_package_v1.txt"
TEMPERATURE: Final = 0.2
MAX_TOKENS: Final = 3_000
REQUEST_TIMEOUT_SECONDS: Final = 30.0


def load_runtime_prompt(path: Path = PROMPT_PATH) -> str:
    try:
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        text = data.decode("utf-8", errors="strict")
    except (OSError, UnicodeError):
        raise F0Error("E_PROMPT_VERSION", "tracked runtime prompt cannot be read") from None
    if digest != PROMPT_SHA256:
        raise F0Error(
            "E_PROMPT_VERSION", "runtime prompt changed without a prompt-version update"
        )
    return text


def create_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        base_url=BASE_URL,
        max_retries=0,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )


def request_completion(client: Any, messages: list[dict[str, str]]) -> Any:
    try:
        return client.chat.completions.create(
            model=MODEL,
            messages=messages,
            stream=False,
            temperature=TEMPERATURE,
            response_format={"type": "json_object"},
            max_tokens=MAX_TOKENS,
            extra_body={"thinking": {"type": "disabled"}},
        )
    except AuthenticationError:
        raise F0Error(
            "E_PROVIDER_AUTH", "DeepSeek authentication or billing rejected the request"
        ) from None
    except RateLimitError:
        raise F0Error("E_PROVIDER_RATE_LIMIT", "DeepSeek rate limit rejected the request") from None
    except APITimeoutError:
        raise F0Error("E_PROVIDER_TIMEOUT", "DeepSeek request timed out") from None
    except APIConnectionError:
        raise F0Error("E_PROVIDER_FAILURE", "DeepSeek connection failed") from None
    except APIStatusError as error:
        if error.status_code in {401, 402, 403}:
            raise F0Error(
                "E_PROVIDER_AUTH", "DeepSeek authentication or billing rejected the request"
            ) from None
        raise F0Error("E_PROVIDER_FAILURE", "DeepSeek server rejected the request") from None

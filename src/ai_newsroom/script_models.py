from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ai_newsroom.models import SourceReference

_WORD = re.compile(r"[0-9A-Za-z\u0400-\u04FF]+(?:[-\u2019'][0-9A-Za-z\u0400-\u04FF]+)*")


def count_spoken_words(value: str) -> int:
    return len(_WORD.findall(value))


class ScriptScene(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    order: int = Field(ge=1, le=8)
    narration: str = Field(min_length=1, max_length=1_500)
    on_screen_text: str = Field(min_length=1, max_length=120)
    source_label: str = Field(min_length=1, max_length=100)
    claim_ids: list[str] = Field(max_length=20)
    visual_kind: Literal["TEXT_CARD"]

    @model_validator(mode="after")
    def validate_claim_ids(self) -> ScriptScene:
        if len(set(self.claim_ids)) != len(self.claim_ids):
            raise ValueError("scene claim IDs must be unique")
        return self


class ProviderSceneDraft(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    narration: str = Field(min_length=1, max_length=1_500)
    on_screen_text: str = Field(min_length=1, max_length=120)
    claim_ids: list[str] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def validate_claim_ids(self) -> ProviderSceneDraft:
        if len(set(self.claim_ids)) != len(self.claim_ids):
            raise ValueError("scene claim IDs must be unique")
        return self


class ProviderScriptDraft(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    working_title: str = Field(min_length=1, max_length=300)
    hook: str = Field(min_length=1, max_length=300)
    scenes: list[ProviderSceneDraft] = Field(min_length=5, max_length=8)
    caption: str = Field(min_length=1, max_length=2_000)

    @model_validator(mode="after")
    def validate_hook(self) -> ProviderScriptDraft:
        if self.scenes[0].narration != self.hook:
            raise ValueError("first scene narration must equal the hook")
        return self


class ProductionScript(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    schema_version: Literal[1]
    script_id: str = Field(pattern=r"^script_[a-f0-9]{24}$")
    story_id: str = Field(pattern=r"^story_[a-f0-9]{24}$")
    package_id: str = Field(pattern=r"^pkg_[a-f0-9]{24}$")
    input_fingerprint: str = Field(pattern=r"^[a-f0-9]{64}$")
    generator: Literal["safe-local-v1"]
    template_version: Literal["claim-safe-script-v1"]
    language: Literal["ru"]
    target_duration_seconds: int = Field(ge=45, le=75)
    working_title: str = Field(min_length=1, max_length=300)
    hook: str = Field(min_length=1, max_length=300)
    spoken_text: str = Field(min_length=1, max_length=6_000)
    word_count: int = Field(ge=90, le=170)
    scenes: list[ScriptScene] = Field(min_length=5, max_length=8)
    source_references: list[SourceReference] = Field(min_length=1, max_length=3)
    limitations: list[str] = Field(min_length=1, max_length=20)
    caption: str = Field(min_length=1, max_length=2_000)
    manual_approval_required: Literal[True]

    @model_validator(mode="after")
    def validate_script_shape(self) -> ProductionScript:
        if [scene.order for scene in self.scenes] != list(range(1, len(self.scenes) + 1)):
            raise ValueError("scene order must be sequential")
        if self.scenes[0].narration != self.hook:
            raise ValueError("first scene narration must equal the hook")
        narration = " ".join(scene.narration for scene in self.scenes)
        if narration != self.spoken_text:
            raise ValueError("spoken_text must equal ordered scene narration")
        if count_spoken_words(self.spoken_text) != self.word_count:
            raise ValueError("word_count does not match spoken_text")
        if re.search(r"[\u0400-\u04FF]", self.spoken_text) is None:
            raise ValueError("spoken_text must contain Russian text")
        return self

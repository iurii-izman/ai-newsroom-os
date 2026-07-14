from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EVIDENCE_LIMITATION = (
    "Доказательная база ограничена содержимым официальной ленты поставщика; "
    "независимая проверка не проводилась."
)


class F0Error(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class SourceSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    id: str
    original_url: str
    canonical_url: str
    title: str
    summary_text: str
    published_at: str | None
    published_at_raw: str | None
    discovered_at: str
    content_hash: str
    source_name: str | None = None


class Story(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    id: str
    primary_source_id: str


class PackageGenerator(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    name: Literal["mock"]
    version: Literal["mock-v1"]


class PackageStory(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    id: str
    title: str


class PackageSource(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    canonical_url: str
    content_hash: str
    id: str
    published_at: str | None
    published_at_raw: str | None
    title: str


class MockClaim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    id: str
    text: str
    type: Literal["VENDOR_CLAIM"]
    status: Literal["UNVERIFIED"]
    source_ids: list[str] = Field(min_length=1, max_length=1)
    qualifier: Literal["Fixture metadata only; no independent or human verification."]


class StoryPackagePayload(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    schema_version: Literal[1]
    package_id: str
    generation_mode: Literal["MOCK"]
    publishable: Literal[False]
    mock_notice: Literal["Demo-only package; no human verification; do not publish."]
    generator: PackageGenerator
    input_fingerprint: str
    story: PackageStory
    sources: list[PackageSource] = Field(min_length=1, max_length=1)
    claims: list[MockClaim] = Field(min_length=1, max_length=1)


class StoryPackageSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    package_id: str
    story_id: str
    schema_version: Literal[1, 2]
    generator_name: Literal["mock", "deepseek"]
    generator_version: Literal["mock-v1", "deepseek-v4-flash"]
    input_fingerprint: str
    payload_json: str
    built_at: str


class BuildGenerator(StrEnum):
    MOCK = "mock"
    DEEPSEEK = "deepseek"


class DeepSeekGenerator(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    provider: Literal["deepseek"]
    model: Literal["deepseek-v4-flash"]
    api_format: Literal["openai-chat-completions"]
    thinking: Literal["disabled"]
    temperature: float = Field(ge=0.2, le=0.2)


class RealClaim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    claim_id: str = Field(pattern=r"^claim_[a-z0-9_]{1,64}$")
    text: str = Field(min_length=1, max_length=2_000)
    status: Literal["VERIFIED", "VENDOR_CLAIM", "INFERENCE", "OPINION", "UNVERIFIED"]
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    evidence_source_id: str
    use_in_script: bool
    qualification: str = Field(min_length=1, max_length=1_000)

    @model_validator(mode="after")
    def enforce_unverified_use(self) -> RealClaim:
        if self.status == "UNVERIFIED" and self.use_in_script:
            raise ValueError("UNVERIFIED claims cannot be used in script")
        return self


class SourceReference(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    source_id: str
    canonical_url: str


class UsageMetadata(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    total_tokens: int | None = Field(default=None, ge=0)
    cache_hit_tokens: int | None = Field(default=None, ge=0)
    repair_used: bool = False


class ProviderStoryPackageDraft(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)

    story_id: str
    source_id: str
    working_title: str = Field(min_length=1, max_length=500)
    editorial_format: Literal["AI_SIGNAL", "TESTED_FOR_YOU", "AI_WORKFLOW"]
    one_sentence_fact: str = Field(min_length=1, max_length=2_000)
    why_it_matters: str = Field(min_length=1, max_length=4_000)
    editorial_angle: str = Field(min_length=1, max_length=4_000)
    claims: list[RealClaim] = Field(min_length=1, max_length=20)
    limitations: list[str] = Field(min_length=1, max_length=20)
    demonstration_plan: list[str] = Field(min_length=1, max_length=20)
    publication_verdict: Literal[
        "READY", "READY_WITH_QUALIFICATION", "NEEDS_TEST", "HOLD", "REJECT"
    ]
    source_references: list[SourceReference] = Field(min_length=1, max_length=1)

    @model_validator(mode="after")
    def enforce_evidence_scope(self) -> ProviderStoryPackageDraft:
        if EVIDENCE_LIMITATION not in self.limitations:
            raise ValueError("feed-only evidence limitation is required")
        if len({claim.claim_id for claim in self.claims}) != len(self.claims):
            raise ValueError("claim IDs must be unique")
        if any(claim.evidence_source_id != self.source_id for claim in self.claims):
            raise ValueError("claim references an unsupplied source")
        reference = self.source_references[0]
        if reference.source_id != self.source_id:
            raise ValueError("source reference does not match supplied source")
        return self


class RealStoryPackagePayload(ProviderStoryPackageDraft):
    schema_version: Literal[2]
    package_id: str
    input_fingerprint: str
    generator: DeepSeekGenerator
    prompt_version: Literal["f1f2-story-package-v1"]
    usage_metadata: UsageMetadata


StoryPackage = StoryPackagePayload | RealStoryPackagePayload

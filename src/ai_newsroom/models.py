from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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

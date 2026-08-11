"""Bedrock Converse generator. Model id is an env var; the call shape does not change."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Protocol


DEFAULT_GEN_MODEL = "amazon.nova-micro-v1:0"


@dataclass(frozen=True)
class Completion:
    text: str
    model_id: str


class Generator(Protocol):
    model_id: str

    def complete(self, system: str, user: str) -> Completion: ...


class BedrockConverse:
    def __init__(self, model_id: str | None = None, region: str | None = None) -> None:
        self.model_id = model_id or os.environ.get("APPRENTICE_GEN_MODEL", DEFAULT_GEN_MODEL)
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")

    def complete(self, system: str, user: str) -> Completion:
        import boto3

        client = boto3.client("bedrock-runtime", region_name=self.region)
        resp = client.converse(
            modelId=self.model_id,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": user}]}],
            inferenceConfig={"temperature": 0, "topP": 1, "maxTokens": 1024},
        )
        parts = resp["output"]["message"]["content"]
        text = "".join(p.get("text", "") for p in parts)
        return Completion(text=text, model_id=self.model_id)


def get_generator() -> Generator:
    kind = os.environ.get("APPRENTICE_GENERATOR", "bedrock").lower()
    if kind in {"bedrock", "converse"}:
        return BedrockConverse()
    raise RuntimeError(
        f"Unknown APPRENTICE_GENERATOR={kind!r}. "
        "Use 'bedrock' or inject a Generator in tests."
    )

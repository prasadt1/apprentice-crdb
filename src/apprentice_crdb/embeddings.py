"""Embedding interface. Mock is labeled and local-only; Bedrock is the production path."""

from __future__ import annotations

import hashlib
import math
import os
from typing import Protocol


DIM = 384


class Embedder(Protocol):
    provider: str

    def embed(self, text: str) -> list[float]: ...


class MockHasher:
    """Deterministic bag-of-bytes vector. Not semantic. Never claim it is Titan."""

    provider = "mock-hasher"

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).digest()
        raw = (digest * ((DIM // len(digest)) + 1))[:DIM]
        vec = [((b / 255.0) * 2.0) - 1.0 for b in raw]
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]


class BedrockTitan:
    provider = "bedrock-titan"

    def __init__(self, region: str | None = None, model_id: str | None = None) -> None:
        self.region = region or os.environ.get("AWS_REGION", "us-east-1")
        self.model_id = model_id or os.environ.get(
            "APPRENTICE_EMBED_MODEL", "amazon.titan-embed-text-v2:0"
        )

    def embed(self, text: str) -> list[float]:
        import json

        import boto3

        client = boto3.client("bedrock-runtime", region_name=self.region)
        resp = client.invoke_model(
            modelId=self.model_id,
            body=json.dumps({"inputText": text, "dimensions": DIM, "normalize": True}),
        )
        payload = json.loads(resp["body"].read())
        return list(payload["embedding"])


def get_embedder() -> Embedder:
    kind = os.environ.get("APPRENTICE_EMBEDDER", "mock").lower()
    if kind in {"bedrock", "titan"}:
        return BedrockTitan()
    return MockHasher()

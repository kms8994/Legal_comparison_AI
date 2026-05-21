from __future__ import annotations

import math

from google import genai
from google.genai import types

from app.core.config import settings


DEFAULT_EMBEDDING_DIMENSION = 1536


class GeminiEmbeddingClient:
    def __init__(self) -> None:
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY 환경변수를 설정해 주세요.")
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def embed_document(self, text: str, dimension: int = DEFAULT_EMBEDDING_DIMENSION) -> list[float]:
        return self._embed(text, task_type="RETRIEVAL_DOCUMENT", dimension=dimension)

    def embed_query(self, text: str, dimension: int = DEFAULT_EMBEDDING_DIMENSION) -> list[float]:
        return self._embed(text, task_type="RETRIEVAL_QUERY", dimension=dimension)

    def _embed(self, text: str, *, task_type: str, dimension: int) -> list[float]:
        result = self.client.models.embed_content(
            model=settings.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=dimension,
            ),
        )
        if not result.embeddings:
            raise RuntimeError("Gemini embedding 응답이 비어 있습니다.")
        values = list(result.embeddings[0].values)
        if settings.embedding_model == "gemini-embedding-001" and dimension != 3072:
            return _normalize(values)
        return values


def _normalize(values: list[float]) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in values))
    if magnitude == 0:
        return values
    return [value / magnitude for value in values]

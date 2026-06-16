from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMResult:
    content_json: dict[str, Any]
    raw_text: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    latency_ms: int


class LLMClient(Protocol):
    def generate_json(self, *, system_prompt: str, user_prompt: str, schema_name: str) -> LLMResult:
        raise NotImplementedError

    def generate_json_with_image(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_path: str | Path,
        schema_name: str,
    ) -> LLMResult:
        raise NotImplementedError

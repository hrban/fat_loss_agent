from __future__ import annotations

import base64
import json
import mimetypes
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

from fat_loss_agent.llm.base import LLMResult


class MissingQwenApiKeyError(RuntimeError):
    pass


class InvalidLLMJsonError(RuntimeError):
    def __init__(self, raw_text: str):
        super().__init__("Qwen returned invalid JSON")
        self.raw_text = raw_text


class QwenClient:
    def __init__(self, *, api_key: str | None, base_url: str, model: str):
        if not api_key:
            raise MissingQwenApiKeyError("QWEN_API_KEY or DASHSCOPE_API_KEY is required")
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def generate_json(self, *, system_prompt: str, user_prompt: str, schema_name: str) -> LLMResult:
        started = time.perf_counter()
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        raw_text = completion.choices[0].message.content or ""
        try:
            content_json: dict[str, Any] = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise InvalidLLMJsonError(raw_text) from exc

        usage = completion.usage
        return LLMResult(
            content_json=content_json,
            raw_text=raw_text,
            provider="qwen",
            model=self.model,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
            latency_ms=latency_ms,
        )

    def generate_json_with_image(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        image_path: str | Path,
        schema_name: str,
    ) -> LLMResult:
        started = time.perf_counter()
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {"type": "image_url", "image_url": {"url": self._image_to_data_url(Path(image_path))}},
                    ],
                },
            ],
            temperature=0.2,
        )
        latency_ms = int((time.perf_counter() - started) * 1000)
        raw_text = completion.choices[0].message.content or ""
        try:
            content_json: dict[str, Any] = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise InvalidLLMJsonError(raw_text) from exc

        usage = completion.usage
        return LLMResult(
            content_json=content_json,
            raw_text=raw_text,
            provider="qwen",
            model=self.model,
            prompt_tokens=getattr(usage, "prompt_tokens", 0) if usage else 0,
            completion_tokens=getattr(usage, "completion_tokens", 0) if usage else 0,
            latency_ms=latency_ms,
        )

    @staticmethod
    def _image_to_data_url(image_path: Path) -> str:
        mime_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

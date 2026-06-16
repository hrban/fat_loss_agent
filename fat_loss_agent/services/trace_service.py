from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fat_loss_agent.repositories.trace_repo import TraceRepository


class TraceService:
    def __init__(self, repo: TraceRepository, jsonl_path: Path):
        self.repo = repo
        self.jsonl_path = jsonl_path

    def record_trace(
        self,
        *,
        user_id: str,
        user_input: str,
        intent: str,
        tool_calls: list[dict[str, Any]],
        llm_provider: str,
        llm_model: str,
        llm_prompt_tokens: int,
        llm_completion_tokens: int,
        llm_latency_ms: int,
        status: str,
        error_message: str,
    ) -> str:
        trace_id = str(uuid.uuid4())
        trace = {
            "user_id": user_id,
            "trace_id": trace_id,
            "user_input": user_input,
            "intent": intent,
            "tool_calls_json": json.dumps(tool_calls, ensure_ascii=False),
            "llm_provider": llm_provider,
            "llm_model": llm_model,
            "llm_prompt_tokens": llm_prompt_tokens,
            "llm_completion_tokens": llm_completion_tokens,
            "llm_latency_ms": llm_latency_ms,
            "status": status,
            "error_message": error_message,
        }
        self.repo.insert(trace)
        self.jsonl_path.parent.mkdir(parents=True, exist_ok=True)
        with self.jsonl_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(trace, ensure_ascii=False) + "\n")
        return trace_id

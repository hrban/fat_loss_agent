from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


DEFAULT_USER_ID = "local_user"


@dataclass(frozen=True)
class AppConfig:
    db_path: Path
    photo_dir: Path
    trace_log_path: Path
    qwen_api_key: str | None
    qwen_base_url: str
    qwen_model: str
    qwen_vision_model: str


def load_config() -> AppConfig:
    load_dotenv()
    db_path = Path(os.getenv("APP_DB_PATH", "fat_loss_agent/data/app.db"))
    photo_dir = Path(os.getenv("PHOTO_DIR", "fat_loss_agent/data/photos"))
    trace_log_path = Path(os.getenv("TRACE_LOG_PATH", "fat_loss_agent/traces/agent_logs.jsonl"))
    qwen_api_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    qwen_model = os.getenv("QWEN_MODEL", "qwen-plus")
    return AppConfig(
        db_path=db_path,
        photo_dir=photo_dir,
        trace_log_path=trace_log_path,
        qwen_api_key=qwen_api_key,
        qwen_base_url=os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
        qwen_model=qwen_model,
        qwen_vision_model=os.getenv("QWEN_VISION_MODEL", qwen_model),
    )

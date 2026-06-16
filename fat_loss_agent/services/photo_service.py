from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path


class UnsupportedPhotoTypeError(ValueError):
    pass


class PhotoService:
    allowed_suffixes = {".jpg", ".jpeg", ".png", ".webp"}

    def __init__(self, photo_dir: Path):
        self.photo_dir = photo_dir

    def save_upload(self, *, user_id: str, original_filename: str, content: bytes) -> Path:
        suffix = Path(original_filename).suffix.lower()
        if suffix not in self.allowed_suffixes:
            raise UnsupportedPhotoTypeError(f"unsupported photo type: {suffix or 'unknown'}")
        if suffix == ".jpeg":
            suffix = ".jpg"

        self.photo_dir.mkdir(parents=True, exist_ok=True)
        safe_user_id = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in user_id)[:64]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        digest = hashlib.sha256(content).hexdigest()[:12]
        path = self.photo_dir / f"{safe_user_id}_{timestamp}_{digest}{suffix}"
        path.write_bytes(content)
        return path

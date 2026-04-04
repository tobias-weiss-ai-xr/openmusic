import hashlib
import json
from pathlib import Path


class CacheManager:
    """Manages caching of generated audio segments to avoid recomputation."""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path.home() / ".cache" / "openmusic" / "acestep"

    def compute_hash(self, prompt: str, params: dict) -> str:
        raw = f"{prompt}:{json.dumps(params, sort_keys=True)}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get_cached(self, prompt_hash: str) -> Path | None:
        entry_dir = self.cache_dir / prompt_hash
        path_file = entry_dir / "path.txt"
        if not path_file.exists():
            return None
        cached_path = Path(path_file.read_text().strip())
        if not cached_path.exists():
            return None
        return cached_path

    def set_cached(self, prompt_hash: str, path: Path) -> None:
        entry_dir = self.cache_dir / prompt_hash
        entry_dir.mkdir(parents=True, exist_ok=True)
        (entry_dir / "path.txt").write_text(str(path))

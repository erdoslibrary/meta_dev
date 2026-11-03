"""Model + environment settings (TRD §2, §6.1). No secrets stored here."""

import os
from pathlib import Path

DEFAULT_MODEL = "muse-spark-1.3"


def _load_dotenv():
    """Minimal .env loader (KEY=VALUE, # comments, quotes stripped).

    Real environment always wins. stdlib only, no new dependency.
    """
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key and key not in os.environ:
            os.environ[key] = value


_load_dotenv()
DEFAULT_SAM_MODEL = "sam-3.1"
DEFAULT_BASE_URL = "https://api.meta.ai/v1"


def model():
    """Chat model name for agent runs and report analysis."""
    return os.environ.get("MODEL_API_MODEL", DEFAULT_MODEL)


def sam_model():
    """Segmentation model name (SAM path, optional)."""
    return os.environ.get("SAM_MODEL", DEFAULT_SAM_MODEL)


def base_url():
    """Model API base URL."""
    return os.environ.get("MODEL_API_BASE_URL", DEFAULT_BASE_URL)


def api_key():
    """API key, or None when absent (callers raise MissingKeyError)."""
    return os.environ.get("MODEL_API_KEY")

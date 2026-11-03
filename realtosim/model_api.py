"""Muse Spark client (TRD §6.1). httpx is imported lazily: importable without it.

Tests inject a FakeClient with `.post(path, **kwargs)` returning an object
with `.status_code`, `.headers`, `.json()`. Transport errors are detected by
httpx isinstance checks when httpx exists, else by exception class name.
"""

import time

from realtosim import settings

MAX_RETRIES = 4
TIMEOUT_SECONDS = 180

RETRYABLE_STATUSES = {408, 409, 429} | set(range(500, 600))
_CONN_ERROR_NAMES = {
    "ConnectError", "TimeoutException", "ConnectTimeout",
    "ReadTimeout", "WriteTimeout", "PoolTimeout",
}


class MissingKeyError(Exception):
    """MODEL_API_KEY is absent."""


class ModelAPIError(Exception):
    """Model call failed (with .status set when it was an HTTP failure)."""

    def __init__(self, message, status=None):
        super().__init__(message)
        self.status = status


def make_client():
    """httpx client for Muse Spark. Raises MissingKeyError without a key."""
    key = settings.api_key()
    if not key:
        raise MissingKeyError("MODEL_API_KEY이 없습니다")
    try:
        import httpx
    except ImportError as e:
        raise ModelAPIError("httpx is not installed") from e
    return httpx.Client(
        base_url=settings.base_url(),
        timeout=TIMEOUT_SECONDS,
        headers={"Authorization": f"Bearer {key}"},
    )


def _is_connection_error(exc):
    try:
        import httpx
        if isinstance(exc, (httpx.ConnectError, httpx.TimeoutException)):
            return True
    except ImportError:
        pass
    return type(exc).__name__ in _CONN_ERROR_NAMES


def _retry_after(headers):
    try:
        value = float(headers.get("Retry-After", ""))
    except (TypeError, ValueError):
        return None
    return value if 0 < value <= 120 else None


def _wait(attempt, headers, sleep):
    """attempt is 0-based. Returns seconds waited (TRD §6.1)."""
    forced = _retry_after(headers or {})
    seconds = forced if forced is not None else min(0.5 * 2 ** attempt, 8)
    sleep(seconds)
    return seconds


def _post(client, path, sleep=time.sleep, **kwargs):
    """POST with retries. 1 initial try + MAX_RETRIES retries."""
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = client.post(path, **kwargs)
        except Exception as exc:  # noqa: BLE001 - transport errors retried by kind
            if _is_connection_error(exc) and attempt < MAX_RETRIES:
                last_error = exc
                _wait(attempt, {}, sleep)
                continue
            raise ModelAPIError(f"연결 실패: {exc}") from exc
        if response.status_code == 200:
            return response
        if response.status_code in RETRYABLE_STATUSES and attempt < MAX_RETRIES:
            last_error = ModelAPIError(f"HTTP {response.status_code}",
                                       status=response.status_code)
            _wait(attempt, response.headers, sleep)
            continue
        raise ModelAPIError(f"HTTP {response.status_code}",
                            status=response.status_code)
    raise ModelAPIError(f"재시도 소진: {last_error}") from last_error


def respond(client, model_name, system, turns, sleep=time.sleep):
    """POST {base}/responses. Collects output_text, else "" (TRD §6.1, #26).

    turns: [{"text": str, "images": [file_id]}]; images go on their own turn.
    """
    messages = [
        {"role": "system",
         "content": [{"type": "input_text", "text": system}]},
    ]
    for turn in turns:
        content = [{"type": "input_text", "text": turn.get("text", "")}]
        for file_id in turn.get("images", []):
            content.append({"type": "input_image", "file_id": file_id})
        messages.append({"role": "user", "content": content})
    payload = {"model": model_name, "input": messages}
    response = _post(client, "/responses", sleep=sleep, json=payload)
    texts = [
        part.get("text", "")
        for item in response.json().get("output", [])
        if item.get("type") == "message"
        for part in item.get("content", [])
        if part.get("type") == "output_text"
    ]
    return "".join(texts)


def upload_file(client, path, sleep=time.sleep):
    """POST {base}/files (multipart file + purpose=user_data). Returns id."""
    from pathlib import Path
    path = Path(path)
    response = _post(
        client, "/files", sleep=sleep,
        files={"file": (path.name, path.read_bytes())},
        data={"purpose": "user_data"},
    )
    return response.json()["id"]

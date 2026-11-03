"""model_api tests with FakeClient. No network (constitution I)."""

import unittest

from realtosim import model_api


class FakeConnectError(Exception):
    pass


# Name-based fallback detection (httpx is absent in the test env).
FakeConnectError.__name__ = "ConnectError"


class FakeResponse:
    def __init__(self, status_code, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload or {}
        self.headers = headers or {}

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    def post(self, path, **kwargs):
        self.calls.append((path, kwargs))
        action = self.script.pop(0)
        if isinstance(action, Exception):
            raise action
        return action


def ok_output(text):
    return FakeResponse(200, {"output": [
        {"type": "message",
         "content": [{"type": "output_text", "text": text}]}]})


class ModelApiTests(unittest.TestCase):
    def test_400_fails_immediately(self):  # TRD #17
        client = FakeClient([FakeResponse(400, {})])
        with self.assertRaises(model_api.ModelAPIError):
            model_api.respond(client, "m", "sys", [{"text": "hi", "images": []}], sleep=lambda s: None)
        self.assertEqual(len(client.calls), 1)

    def test_503_retries_five_times(self):  # TRD #24
        waits = []
        client = FakeClient([FakeResponse(503, {})] * 5)
        with self.assertRaises(model_api.ModelAPIError):
            model_api.respond(client, "m", "sys", [{"text": "hi", "images": []}], sleep=waits.append)
        self.assertEqual(len(client.calls), 5)
        self.assertEqual(waits, [0.5, 1.0, 2.0, 4.0])

    def test_429_retry_after_then_success(self):  # TRD #25
        waits = []
        client = FakeClient([
            FakeResponse(429, {}, {"Retry-After": "3"}),
            ok_output("{\"action\": \"answer\"}"),
        ])
        text = model_api.respond(client, "m", "sys", [{"text": "hi", "images": []}], sleep=waits.append)
        self.assertEqual(waits, [3.0])
        self.assertIn("answer", text)

    def test_empty_output_is_empty_string(self):  # TRD #26
        client = FakeClient([FakeResponse(200, {"output": []})])
        self.assertEqual(
            model_api.respond(client, "m", "sys", [{"text": "hi", "images": []}], sleep=lambda s: None),
            "")

    def test_connection_error_retries_then_success(self):
        waits = []
        client = FakeClient([FakeConnectError("down"), ok_output("hi")])
        text = model_api.respond(client, "m", "sys", [{"text": "hi", "images": []}], sleep=waits.append)
        self.assertEqual(text, "hi")
        self.assertEqual(waits, [0.5])

    def test_missing_key(self):
        import os
        old = os.environ.pop("MODEL_API_KEY", None)
        try:
            with self.assertRaises(model_api.MissingKeyError):
                model_api.make_client()
        finally:
            if old is not None:
                os.environ["MODEL_API_KEY"] = old

    def test_upload_returns_id(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "x.jpg"
            p.write_bytes(b"img")
            client = FakeClient([FakeResponse(200, {"id": "file-1"})])
            self.assertEqual(
                model_api.upload_file(client, p, sleep=lambda s: None),
                "file-1")
            path, kwargs = client.calls[0]
            self.assertEqual(path, "/files")
            self.assertEqual(kwargs["data"], {"purpose": "user_data"})


if __name__ == "__main__":
    unittest.main()

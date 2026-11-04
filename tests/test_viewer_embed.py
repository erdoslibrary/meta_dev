"""T035: embed.py exposure (allowed/excluded fields, data.js audit).

Contract: contracts/viewer.md Data Generation. embed.py validates each
schema-required log original (before reason removal) against
log.schema.json and creates no data.js on failure. Playback-refusal
samples are excluded from that gate but included in data.js with the same
allow/exclude rules. Allowed includes on_correct and
answer_submitted.value; the banned answer target is the puzzle.json answer
field only (event values are kept).
"""

import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_JS = ROOT / "viewer" / "dist" / "data.js"

ALWAYS_BANNED_KEYS = {"sha256", "next_object_id", "tone", "hints", "reason"}


def _load_embed():
    spec = importlib.util.spec_from_file_location(
        "viewer_embed", ROOT / "viewer" / "tools" / "embed.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _walk(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _walk(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk(item)


def _payload_events(payload):
    for section in ("testdata", "refusal"):
        for log in (payload.get(section) or {}).values():
            yield from log.get("events", [])
    for entry in (payload.get("sets") or {}).values():
        for log in entry.get("logs", {}).values():
            yield from log.get("events", [])


class EmbedExposureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.embed = _load_embed()
        cls.payload = cls.embed.build_payload()

    def test_payload_removes_reason(self):
        leaked = [e for e in _payload_events(self.payload) if "reason" in e]
        self.assertFalse(leaked, f"reason leaked into payload: {leaked[:2]}")

    def test_payload_excludes_always_banned_keys(self):
        found = set()
        for node in _walk(self.payload):
            found |= ALWAYS_BANNED_KEYS & set(node)
        self.assertFalse(found, f"banned keys in payload: {found}")

    def test_payload_keeps_allowed_submission_values(self):
        values = [
            e.get("value")
            for e in _payload_events(self.payload)
            if e.get("type") == "answer_submitted"
        ]
        self.assertTrue(values, "no answer_submitted events in payload")
        self.assertTrue(all(v for v in values), "answer_submitted.value stripped")

    def test_payload_keeps_on_correct(self):
        texts = [
            p.get("on_correct")
            for entry in (self.payload.get("sets") or {}).values()
            for p in entry.get("puzzle", {}).get("puzzles", [])
        ]
        self.assertTrue(texts, "no puzzle entries in payload")
        self.assertTrue(all(texts), "on_correct stripped from payload")

    def test_drunkard_set_has_no_failed_answers(self):
        # No real log ends failed, so no puzzle.json answer/next_instruction
        # may appear anywhere under sets/drunkard-set.
        section = self.payload["sets"]["drunkard-set"]
        keys = set()
        for node in _walk(section):
            keys |= {"answer", "next_instruction"} & set(node)
        self.assertFalse(keys, f"non-failed answers in payload: {keys}")

    def test_refusal_samples_included_with_defects(self):
        refusal = self.payload.get("refusal") or {}
        self.assertTrue(refusal, "no playback-refusal samples in payload")
        for name, log in refusal.items():
            events = log.get("events", [])
            Ts = [e["t"] for e in events]
            gap = any(b - a != 1 for a, b in zip(Ts, Ts[1:]))
            self.assertTrue(
                gap or (events and events[-1].get("type") != "end"),
                f"refusal sample {name} lost its defect",
            )
            self.assertFalse(
                [e for e in events if "reason" in e],
                f"reason leaked into refusal sample {name}",
            )

    def test_data_js_audit(self):
        text = DATA_JS.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("window.RT_DATA = "))
        self.assertTrue(text.rstrip().endswith(";"))
        payload = json.loads(text[len("window.RT_DATA = "):].rstrip().rstrip(";"))
        found = set()
        for node in _walk(payload):
            found |= ALWAYS_BANNED_KEYS & set(node)
        self.assertFalse(found, f"banned keys in data.js: {found}")


if __name__ == "__main__":
    unittest.main()

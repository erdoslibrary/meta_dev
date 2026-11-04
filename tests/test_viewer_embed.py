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
import shutil
import tempfile
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
        # Decision E: shared puzzle has no answer/next_instruction; reveals[key]
        # holds answers only for puzzles that ended failed in that log.
        section = self.payload["sets"]["drunkard-set"]
        keys = set()
        for node in _walk(section["puzzle"]):
            keys |= {"answer", "next_instruction"} & set(node)
        self.assertFalse(keys, f"shared puzzle answers in payload: {keys}")
        reveals = section.get("reveals", {})
        for key, log in section["logs"].items():
            failed = {str(n) for n in self.embed.failed_numbers(log)}
            self.assertEqual(set(reveals.get(key, {})), failed)

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


def _walk_keys(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            yield obj[key]
        for value in obj.values():
            yield from _walk_keys(value, key)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_keys(item, key)


class DialogueHintTests(unittest.TestCase):
    """Dialogue keeps text only; contains_hint is excluded everywhere."""

    @classmethod
    def setUpClass(cls):
        cls.embed = _load_embed()
        cls.payload = cls.embed.build_payload()

    def test_payload_has_no_contains_hint(self):
        found = list(_walk_keys(self.payload, "contains_hint"))
        self.assertFalse(found, f"contains_hint leaked into payload: {found[:2]}")

    def test_data_js_has_no_contains_hint(self):
        text = DATA_JS.read_text(encoding="utf-8")
        self.assertNotIn('"contains_hint"', text)


class PerLogFailedTests(unittest.TestCase):
    """Failed answers follow each log's own puzzle_ended(failed) (T006)."""

    @classmethod
    def setUpClass(cls):
        cls.embed = _load_embed()
        cls.payload = cls.embed.build_payload()

    def _puzzle_doc(self):
        return {
            "puzzles": [
                {
                    "number": 1,
                    "answer": "A1",
                    "next_instruction": "N1",
                    "dialogue": [{"text": "t1"}],
                },
                {
                    "number": 2,
                    "answer": "A2",
                    "next_instruction": None,
                    "dialogue": [{"text": "t2"}],
                },
            ]
        }

    def test_filter_puzzle_keeps_only_failed_answers(self):
        out = self.embed.filter_puzzle(self._puzzle_doc(), {1})
        by_number = {p["number"]: p for p in out["puzzles"]}
        self.assertEqual(by_number[1].get("answer"), "A1")
        self.assertEqual(by_number[1].get("next_instruction"), "N1")
        self.assertNotIn("answer", by_number[2])
        self.assertNotIn("next_instruction", by_number[2])

    def test_filter_puzzle_with_no_failed_drops_all_answers(self):
        out = self.embed.filter_puzzle(self._puzzle_doc(), set())
        for entry in out["puzzles"]:
            self.assertNotIn("answer", entry)
            self.assertNotIn("next_instruction", entry)

    def test_filter_puzzle_drops_null_next_instruction(self):
        out = self.embed.filter_puzzle(self._puzzle_doc(), {1, 2})
        by_number = {p["number"]: p for p in out["puzzles"]}
        self.assertEqual(by_number[2].get("answer"), "A2")
        self.assertNotIn("next_instruction", by_number[2])

    def test_sample_sets_reveals_match_linked_logs(self):
        sets = self.payload.get("sample_sets") or {}
        failed = sets["viewer-failed"]
        for puzzle in failed["puzzle"]["puzzles"]:
            self.assertNotIn("answer", puzzle)
            self.assertNotIn("next_instruction", puzzle)
        reveals = failed["reveals"]
        self.assertEqual(set(reveals.get("testdata/failed", {})), {"1", "2"})
        one = reveals["testdata/failed"]["1"]
        self.assertTrue(one.get("answer"))
        self.assertIn("next_instruction", one)
        two = reveals["testdata/failed"]["2"]
        self.assertTrue(two.get("answer"))
        self.assertNotIn("next_instruction", two)
        multi = sets["viewer-multilayer"]
        for puzzle in multi["puzzle"]["puzzles"]:
            self.assertNotIn("answer", puzzle)
            self.assertNotIn("next_instruction", puzzle)
        self.assertEqual(multi["reveals"].get("testdata/multilayer", {}), {})

    def test_testdata_sample_logs_checked_per_log(self):
        """Each embedded sample log checks its own failed set in the
        linked set's reveals (keys testdata/<name>, number keys strings).

        Sample logs linked to a data/ set land in sets/<id>/reveals;
        the key itself must exist (no .get default).
        """
        payload = self.payload
        for name, log in payload["testdata"].items():
            failed = {str(n) for n in self.embed.failed_numbers(log)}
            psid = log.get("puzzle_set_id")
            if psid in payload["sample_sets"]:
                reveals = payload["sample_sets"][psid]["reveals"]
            else:
                reveals = payload["sets"][psid]["reveals"]
            key = f"testdata/{name}"
            self.assertIn(key, reveals)
            self.assertEqual(set(reveals[key]), failed)
            if failed:
                one = reveals[key]["1"]
                self.assertTrue(one.get("answer"))

    def test_refusal_samples_have_own_reveals_keys(self):
        """Refusal samples resolve like other logs (keys refusal/<name>)."""
        payload = self.payload
        for name, log in payload["refusal"].items():
            failed = self.embed.failed_numbers(log)
            self.assertEqual(failed, set())
            reveals = payload["sets"][log["puzzle_set_id"]]["reveals"]
            key = f"refusal/{name}"
            self.assertIn(key, reveals)
            self.assertEqual(reveals[key], {})

    def test_data_linked_sample_log_reveals(self):
        """A top-level sample log linked to a data/ set lands its answers
        in sets/<id>/reveals under testdata/<name>."""
        root = _make_tmp_root("data-linked-sample")
        self.addCleanup(shutil.rmtree, root, True)
        payload = self.embed.build_payload(root=root)
        entry = payload["sets"]["dset"]
        for puzzle in entry["puzzle"]["puzzles"]:
            self.assertNotIn("answer", puzzle)
            self.assertNotIn("next_instruction", puzzle)
        reveals = entry["reveals"]
        self.assertIn("testdata/fx", reveals)
        self.assertEqual(set(reveals["testdata/fx"]), {"1"})
        one = reveals["testdata/fx"]["1"]
        self.assertTrue(one.get("answer"))
        self.assertIn("next_instruction", one)

    def test_failed_filtering_is_per_log_decision_e(self):
        """Decision E: the shared set puzzle carries no answer or
        next_instruction; per-log answers live in reveals/<log key> for
        failed puzzles only (null next_instruction omitted)."""
        root = _make_tmp_root("per-log")
        self.addCleanup(shutil.rmtree, root, True)
        payload = self.embed.build_payload(root=root)
        entry = payload["sets"]["mixset"]
        for puzzle in entry["puzzle"]["puzzles"]:
            self.assertNotIn("answer", puzzle)
            self.assertNotIn("next_instruction", puzzle)
        reveals = entry["reveals"]
        self.assertEqual(set(reveals["a"]), {"1"})
        self.assertTrue(reveals["a"]["1"].get("answer"))
        self.assertIn("next_instruction", reveals["a"]["1"])
        self.assertEqual(reveals["b"], {})


def _only_puzzle_1(doc):
    """Narrow a copied sample log to puzzle 1 events (plus the end)."""
    events = [e for e in doc["events"] if e.get("puzzle") == 1 or e.get("type") == "end"]
    for i, event in enumerate(events, 1):
        event["t"] = i
    doc["events"] = events
    return doc


def _make_tmp_root(case: str) -> Path:
    """Minimal repo root: one log plus set sources per case."""
    root = Path(tempfile.mkdtemp(prefix="viewer-embed-"))
    testdata = root / "viewer" / "testdata"
    log_src = ROOT / "viewer" / "testdata" / "failed.json"
    static_src = ROOT / "viewer" / "testdata" / "sets" / "viewer-failed"
    doc = json.loads(log_src.read_text(encoding="utf-8"))
    if case == "duplicate":
        doc["puzzle_set_id"] = "dup-set"
        testdata.mkdir(parents=True)
        (testdata / "dup-log.json").write_text(
            json.dumps(doc, ensure_ascii=False), encoding="utf-8"
        )
        for base in (testdata / "sets" / "dup-set", root / "data" / "dup-set"):
            base.mkdir(parents=True)
            for name in ("space", "puzzle", "npc"):
                shutil.copy(static_src / f"{name}.json", base / f"{name}.json")
    elif case == "missing":
        doc["puzzle_set_id"] = "no-such-set"
        testdata.mkdir(parents=True)
        (testdata / "lonely-log.json").write_text(
            json.dumps(doc, ensure_ascii=False), encoding="utf-8"
        )
    elif case == "per-log":
        # Same set, two logs: a.json fails puzzle 1, b.json solves it.
        log_dir = root / "logs" / "mixset"
        log_dir.mkdir(parents=True)
        doc = _only_puzzle_1(doc)
        doc["puzzle_set_id"] = "mixset"
        (log_dir / "a.json").write_text(
            json.dumps(doc, ensure_ascii=False), encoding="utf-8"
        )
        solved = _only_puzzle_1(json.loads(log_src.read_text(encoding="utf-8")))
        solved["puzzle_set_id"] = "mixset"
        for event in solved["events"]:
            if event.get("type") == "answer_submitted":
                event["correct"] = True
            elif event.get("type") == "puzzle_ended":
                event["result"] = "solved_by_dialogue"
        (log_dir / "b.json").write_text(
            json.dumps(solved, ensure_ascii=False), encoding="utf-8"
        )
        data_dir = root / "data" / "mixset"
        data_dir.mkdir(parents=True)
        for name in ("space", "puzzle", "npc"):
            shutil.copy(static_src / f"{name}.json", data_dir / f"{name}.json")
    elif case == "data-linked-sample":
        # No logs/ dir: one top-level sample log linked to a data/ set.
        doc = _only_puzzle_1(doc)
        doc["puzzle_set_id"] = "dset"
        testdata.mkdir(parents=True)
        (testdata / "fx.json").write_text(
            json.dumps(doc, ensure_ascii=False), encoding="utf-8"
        )
        data_dir = root / "data" / "dset"
        data_dir.mkdir(parents=True)
        for name in ("space", "puzzle", "npc"):
            shutil.copy(static_src / f"{name}.json", data_dir / f"{name}.json")
    return root


class SetLookupTests(unittest.TestCase):
    """Each log's puzzle_set_id resolves to sets/<id> or data/<id>.

    Both existing or neither existing must refuse: no data.js (T006).
    Lookup covers every embedded log (logs/ + top-level testdata +
    refusal/); refusal/ samples follow the same rule (contracts/viewer.md).
    """

    @classmethod
    def setUpClass(cls):
        cls.embed = _load_embed()

    def test_real_repo_has_no_lookup_violations(self):
        errors = self.embed.set_lookup_errors()
        self.assertFalse(errors, f"set lookup violations: {errors}")

    def test_duplicate_set_id_is_an_error(self):
        root = _make_tmp_root("duplicate")
        self.addCleanup(shutil.rmtree, root, True)
        errors = self.embed.set_lookup_errors(root=root)
        self.assertIn("dup-set", errors)

    def test_missing_set_id_is_an_error(self):
        root = _make_tmp_root("missing")
        self.addCleanup(shutil.rmtree, root, True)
        errors = self.embed.set_lookup_errors(root=root)
        self.assertIn("no-such-set", errors)

    def test_duplicate_writes_no_data_js(self):
        before = DATA_JS.read_bytes()
        root = _make_tmp_root("duplicate")
        self.addCleanup(shutil.rmtree, root, True)
        rc = self.embed.main(root=root)
        self.assertNotEqual(rc, 0)
        self.assertFalse((root / "viewer" / "dist" / "data.js").exists())
        self.assertEqual(DATA_JS.read_bytes(), before)

    def test_missing_writes_no_data_js(self):
        before = DATA_JS.read_bytes()
        root = _make_tmp_root("missing")
        self.addCleanup(shutil.rmtree, root, True)
        rc = self.embed.main(root=root)
        self.assertNotEqual(rc, 0)
        self.assertFalse((root / "viewer" / "dist" / "data.js").exists())
        self.assertEqual(DATA_JS.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()

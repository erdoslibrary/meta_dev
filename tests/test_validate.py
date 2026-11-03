"""Validator + oracle tests. No model, no network (constitution I)."""

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from realtosim import oracle, validate
from realtosim.validate import SCHEMA_DIR, SCHEMA_NAMES, load_json

SET = Path(__file__).resolve().parent.parent / "data" / "drunkard-set"


def _copy_set(tmp):
    dest = Path(tmp) / "broken-set"
    shutil.copytree(SET, dest)
    return dest


def _rewrite(path, mutate):
    doc = load_json(path)
    mutate(doc)
    path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")


class ValidateTests(unittest.TestCase):
    def test_drunkard_set_passes(self):
        passed, results = validate.check(SET)
        self.assertTrue(passed, results)
        self.assertTrue(all(r["ok"] for r in results))

    def test_broken_chain_fails_m4(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = _copy_set(tmp)
            _rewrite(dest / "puzzle.json",
                     lambda d: d["puzzles"][0].update(object_id="ghost@Z9"))
            passed, results = validate.check(dest)
            self.assertFalse(passed)
            m4 = next(r for r in results if r["check"] == "M4")
            self.assertFalse(m4["ok"])

    def test_broken_letter_count_fails_m6(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = _copy_set(tmp)
            _rewrite(dest / "puzzle.json",
                     lambda d: d["puzzles"][0].update(answer_letter_count=3))
            passed, results = validate.check(dest)
            self.assertFalse(passed)
            m6 = next(r for r in results if r["check"] == "M6")
            self.assertFalse(m6["ok"])

    def test_replica_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            passed, results = validate.check(SET)
            out = Path(tmp) / "replica.md"
            validate.write_replica(out, "drunkard-set", passed, results)
            text = out.read_text(encoding="utf-8")
            self.assertIn("판정: 통과", text)
            self.assertIn("## 수정 항목", text)
            self.assertIn("## 확인 항목", text)


class OracleTests(unittest.TestCase):
    def test_oracle_completes_by_dialogue(self):
        log = oracle.run(SET, "drunkard-set")
        self.assertEqual(log["run_id"], "r0")
        self.assertEqual(log["model"], "oracle")
        ended = [e for e in log["events"] if e["type"] == "puzzle_ended"]
        self.assertTrue(ended)
        for e in ended:
            self.assertEqual(e["result"], "solved_by_dialogue")
        self.assertEqual(log["events"][-1]["type"], "end")
        self.assertEqual(log["events"][-1]["outcome"], "completed")

    def test_oracle_log_passes_schema(self):
        from referencing import Registry, Resource
        schemas = {n: load_json(SCHEMA_DIR / f"{n}.schema.json")
                   for n in SCHEMA_NAMES}
        registry = Registry().with_resources(
            (s["$id"], Resource.from_contents(s)) for s in schemas.values())
        v = Draft202012Validator(schemas["log"], registry=registry)
        log = copy.deepcopy(oracle.run(SET, "drunkard-set"))
        self.assertEqual(list(v.iter_errors(log)), [])




if __name__ == "__main__":
    unittest.main()

"""Runner tests with scripted model. No network (constitution I)."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from realtosim import model_api, run_agents
from realtosim.validate import SCHEMA_DIR, SCHEMA_NAMES, load_json

SET = Path(__file__).resolve().parent.parent / "data" / "drunkard-set"
SPACE = load_json(SET / "space.json")
PUZZLES = load_json(SET / "puzzle.json")
PERSONA = {"age": 30, "job": "tester", "vocab": "중",
           "thinking": "연상을 따라감"}


class ScriptedModel:
    """move -> view -> answer per puzzle, using known answers."""

    def __init__(self, puzzle_set):
        self.answers = {p["object_id"]: p["answer"] for p in puzzle_set["puzzles"]}
        self.objects = [(p["object_id"],
                         p["object_id"].split("@")[1].split(":")[0])
                        for p in puzzle_set["puzzles"]]
        self.step = 0

    def __call__(self, system, turns):
        obs = json.loads(turns[-1]["text"])["observation"]
        if obs["puzzle"] is not None:
            number = obs["puzzle"]["number"]
            target = self.objects[number - 1][0]
            return json.dumps({"action": "answer", "value": self.answers[target],
                               "reason": "scripted"})
        if obs["opened_object_ids"]:
            return json.dumps({"action": "view",
                               "value": obs["opened_object_ids"][0],
                               "reason": "scripted"})
        cell = self.objects[0][1]
        return json.dumps({"action": "move", "value": cell, "reason": "scripted"})


def log_schema_validator():
    from referencing import Registry, Resource
    schemas = {n: load_json(SCHEMA_DIR / f"{n}.schema.json")
               for n in SCHEMA_NAMES}
    registry = Registry().with_resources(
        (s["$id"], Resource.from_contents(s)) for s in schemas.values())
    return Draft202012Validator(schemas["log"], registry=registry)


class RunAgentsTests(unittest.TestCase):
    def test_scripted_run_completes_and_validates(self):
        log = run_agents.run_once(
            SPACE, PUZZLES, PERSONA, run_id="r01", model_name="fake",
            seed=0, respond_fn=ScriptedModel(PUZZLES),
            image_ids={}, max_actions=50)
        self.assertEqual(log["events"][-1]["outcome"], "completed")
        self.assertEqual(list(log_schema_validator().iter_errors(log)), [])

    def test_api_error_aborts(self):  # TRD §6.1
        def boom(system, turns):
            raise model_api.ModelAPIError("down")

        log = run_agents.run_once(
            SPACE, PUZZLES, PERSONA, run_id="r01", model_name="fake",
            seed=0, respond_fn=boom, image_ids={})
        self.assertEqual(log["events"][-1]["type"], "end")
        self.assertEqual(log["events"][-1]["outcome"], "api_error")
        self.assertEqual(len(log["events"]), 1)

    def _tiny_set(self, tmp):
        import hashlib
        data = tmp / "data" / "s"
        (data / "photos").mkdir(parents=True)
        art = data / "p.png"
        art.write_bytes(b"img")
        photo = data / "photos" / "box.jpg"
        photo.write_bytes(b"pic")
        space = {"space_id": "sp", "floors": [
            {"id": "1F", "walls": [{"from": {"x": 0, "y": 0},
                                    "to": {"x": 1, "y": 0}}],
             "doors": [{"id": "d", "from": {"x": 0, "y": 0},
                        "to": {"x": 1, "y": 0}}],
             "meters_per_pixel": 0.1, "origin_px": {"x": 0, "y": 0},
             "columns": 6, "rows": 6}],
            "rooms": [],
            "objects": [{"id": "box@B2", "label": "box", "cells": "B2",
                         "description": "", "photos": ["box.jpg"],
                         "state": "locked"}]}
        puzzle_set = {"puzzle_set_id": "s", "space_id": "sp",
                      "start_cell": "A1", "puzzles": [
                          {"number": 1, "object_id": "box@B2", "npc": "n",
                           "dialogue": [{"text": "hi", "contains_hint": False}],
                           "image": {"path": "p.png", "sha256":
                                     hashlib.sha256(b"img").hexdigest()},
                           "question": "q", "answer": "yes",
                           "answer_letter_count": 3,
                           "hints": [{"level": 1, "after_wrong": 1,
                                      "text": "h"}],
                           "next_instruction": None,
                           "next_object_id": None}]}
        (data / "space.json").write_text(json.dumps(space), encoding="utf-8")
        (data / "puzzle.json").write_text(json.dumps(puzzle_set),
                                          encoding="utf-8")
        return tmp / "data", tmp / "logs"

    def _play_script(self, n_runs):
        from tests.test_model_api import FakeResponse, ok_output
        script = [FakeResponse(200, {"id": "f1"}),
                  FakeResponse(200, {"id": "f2"})]
        for _ in range(n_runs):
            script.append(ok_output(
                '{"action": "move", "value": "B2", "reason": "s"}'))
            script.append(ok_output(
                '{"action": "view", "value": "box@B2", "reason": "s"}'))
            script.append(ok_output(
                '{"action": "answer", "value": "yes", "reason": "s"}'))
        return script

    def test_start_offset_appends_without_touching_earlier(self):
        from tests.test_model_api import FakeClient
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            data_dir, logs_dir = self._tiny_set(tmp)
            (logs_dir / "s").mkdir(parents=True)
            old = logs_dir / "s" / "r01.json"
            old.write_text('{"kept": true}', encoding="utf-8")
            client = FakeClient(self._play_script(2))
            run_agents.run_set("s", 2, 0, data_dir=data_dir,
                               logs_dir=logs_dir, client=client,
                               cache_path=tmp / "cache.json", start=1)
            self.assertEqual(json.loads(old.read_text()),
                             {"kept": True})
            self.assertTrue((logs_dir / "s" / "r02.json").is_file())
            self.assertTrue((logs_dir / "s" / "r03.json").is_file())

    def test_refuses_to_overwrite(self):
        from tests.test_model_api import FakeClient, FakeResponse
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            data_dir, logs_dir = self._tiny_set(tmp)
            (logs_dir / "s").mkdir(parents=True)
            (logs_dir / "s" / "r01.json").write_text("{}", encoding="utf-8")
            client = FakeClient([FakeResponse(200, {"id": "f1"})])
            with self.assertRaises(FileExistsError):
                run_agents.run_set("s", 1, 0, data_dir=data_dir,
                                   logs_dir=logs_dir, client=client,
                                   cache_path=tmp / "cache.json", start=0)

    def test_same_sha_uploads_once(self):  # TRD #27
        from tests.test_model_api import FakeClient, FakeResponse
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / "a.jpg").write_bytes(b"same")
            (tmp / "b.jpg").write_bytes(b"same")
            space = {"objects": [{"id": "x@A1", "photos": ["b.jpg"]}]}

            calls = []

            class Client(FakeClient):
                pass

            client = FakeClient([FakeResponse(200, {"id": "file-9"})])
            orig_post = client.post

            def post(path, **kwargs):
                calls.append(path)
                return orig_post(path, **kwargs)

            client.post = post
            ids = run_agents.prepare_images(
                tmp,
                {"puzzles": [{"image": {
                    "path": "a.jpg",
                    "sha256": hashlib.sha256(b"same").hexdigest()}}]},
                space, client, cache_path=tmp / "cache.json")
            self.assertEqual(ids, {"a.jpg": "file-9", "b.jpg": "file-9"})
            self.assertEqual(calls, ["/files"])


if __name__ == "__main__":
    unittest.main()

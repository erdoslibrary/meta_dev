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

"""T036: viewer schema-required log samples pass log.schema.json.

Scope: top-level viewer/testdata/*.json only. Subdirectories (refusal/,
sets/) and static data files are excluded (contracts/viewer.md).
"""

import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from realtosim.validate import SCHEMA_DIR, SCHEMA_NAMES, load_json

TESTDATA = Path(__file__).resolve().parent.parent / "viewer" / "testdata"


def _registry():
    schemas = {n: load_json(SCHEMA_DIR / f"{n}.schema.json") for n in SCHEMA_NAMES}
    registry = Registry().with_resources(
        (s["$id"], Resource.from_contents(s)) for s in schemas.values()
    )
    return registry, schemas


class ViewerTestdataTests(unittest.TestCase):
    def test_top_level_samples_pass_log_schema(self):
        registry, schemas = _registry()
        validator = Draft202012Validator(schemas["log"], registry=registry)
        samples = sorted(TESTDATA.glob("*.json"))
        self.assertTrue(samples, "no top-level viewer/testdata/*.json samples")
        errors = {}
        for path in samples:
            msgs = [e.message for e in validator.iter_errors(load_json(path))]
            if msgs:
                errors[path.name] = msgs
        self.assertFalse(
            errors, f"schema-required samples failing log.schema.json: {errors}"
        )


if __name__ == "__main__":
    unittest.main()

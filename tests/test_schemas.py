"""docs/schemas/의 스키마와 표본을 검증한다.

표본 파일 이름은 `<스키마>.<설명>.json`이다. invalid 표본은 결함을 하나만 담으므로
오류도 정확히 하나여야 한다. 다른 이유로 거절되는 표본을 잡아내기 위한 조건이다.

실행: python -m unittest discover tests -v
"""

import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SCHEMA_DIR = Path(__file__).resolve().parent.parent / "docs" / "schemas"
EXAMPLE_DIR = SCHEMA_DIR / "examples"
SCHEMA_NAMES = ("space", "puzzle", "persona", "log", "baseline", "npc")


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


SCHEMAS = {name: load(SCHEMA_DIR / f"{name}.schema.json") for name in SCHEMA_NAMES}
REGISTRY = Registry().with_resources(
    (schema["$id"], Resource.from_contents(schema)) for schema in SCHEMAS.values()
)


def errors_for(path):
    name = path.name.split(".")[0]
    validator = Draft202012Validator(SCHEMAS[name], registry=REGISTRY)
    return list(validator.iter_errors(load(path)))


class SchemaTests(unittest.TestCase):
    def test_schemas_are_valid(self):
        for name, schema in SCHEMAS.items():
            with self.subTest(schema=name):
                Draft202012Validator.check_schema(schema)

    def test_every_schema_has_both_kinds_of_example(self):
        for kind in ("valid", "invalid"):
            for name in SCHEMA_NAMES:
                with self.subTest(kind=kind, schema=name):
                    self.assertTrue(list((EXAMPLE_DIR / kind).glob(f"{name}.*.json")))

    def test_valid_examples_pass(self):
        for path in sorted((EXAMPLE_DIR / "valid").glob("*.json")):
            with self.subTest(example=path.name):
                self.assertEqual([e.message for e in errors_for(path)], [])

    def test_invalid_examples_fail_for_one_reason(self):
        for path in sorted((EXAMPLE_DIR / "invalid").glob("*.json")):
            with self.subTest(example=path.name):
                self.assertEqual(len(errors_for(path)), 1)


if __name__ == "__main__":
    unittest.main()

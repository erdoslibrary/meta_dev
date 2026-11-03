"""Persona tests. No model, no network."""

import unittest
from collections import Counter

from jsonschema import Draft202012Validator

from realtosim import personas
from realtosim.personas import SCHEMA


class PersonaTests(unittest.TestCase):
    def test_fifteen_with_five_each_thinking(self):  # TRD §7, M14
        group = personas.generate(15, seed=42)
        self.assertEqual(len(group), 15)
        counts = Counter(p["thinking"] for p in group)
        self.assertEqual(counts, {t: 5 for t in personas.THINKING})

    def test_schema_valid(self):
        validator = Draft202012Validator(SCHEMA)
        for p in personas.generate(15, seed=7):
            self.assertEqual(list(validator.iter_errors(p)), [])

    def test_teens_are_students(self):
        for p in personas.generate(60, seed=3):
            if p["age"] < 20:
                self.assertEqual(p["job"], "학생")
            self.assertNotIn("name", p)

    def test_seed_reproducible(self):
        self.assertEqual(personas.generate(15, seed=11),
                         personas.generate(15, seed=11))
        self.assertNotEqual(personas.generate(15, seed=11),
                            personas.generate(15, seed=12))


if __name__ == "__main__":
    unittest.main()

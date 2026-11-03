"""Persona generation: fixed in front of the run with random.Random(seed).

TRD §7: thinking 3 values x5 shuffled into 15 slots; age 10-79 uniform;
teens are students; vocab uniform; no name. Every persona passes
persona.schema.json and is stored whole in its run log.
"""

import random
from pathlib import Path

from jsonschema import Draft202012Validator

from realtosim.validate import load_json

THINKING = ["문자 그대로 읽음", "말장난을 먼저 떠올림", "연상을 따라감"]
VOCABS = ["상", "중", "하"]
ADULT_JOBS = ["개발자", "약사", "교사", "요리사", "운전기사", "디자이너",
              "간호사", "농부", "판매원", "공무원", "연구원"]

SCHEMA = load_json(Path(__file__).resolve().parent.parent
                    / "docs" / "schemas" / "persona.schema.json")


def generate(count=15, seed=0):
    """Deterministic persona list (TRD §7)."""
    rng = random.Random(seed)
    per_value = (count + len(THINKING) - 1) // len(THINKING)
    deck = [t for t in THINKING for _ in range(per_value)][:count]
    rng.shuffle(deck)
    personas = []
    for thinking in deck:
        age = rng.randint(10, 79)
        job = "학생" if age < 20 else rng.choice(ADULT_JOBS)
        persona = {"age": age, "job": job,
                   "vocab": rng.choice(VOCABS), "thinking": thinking}
        errors = list(Draft202012Validator(SCHEMA).iter_errors(persona))
        if errors:
            raise ValueError(f"persona schema fail: {errors[0].message}")
        personas.append(persona)
    return personas

"""TRD §10 engine contract tests (#1~#16, #18~#23, #28, #29) + exposure + log checks.

Inputs are docs/schemas/examples/valid/ samples only (no model/key/network).
Rejection sentences must match TRD §4 verbatim.
Run: python -m unittest tests.test_game_engine -v
"""

import copy
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from realtosim import game_engine as ge

EXAMPLE_DIR = Path(__file__).resolve().parent.parent / "docs" / "schemas" / "examples" / "valid"
SCHEMA_DIR = Path(__file__).resolve().parent.parent / "docs" / "schemas"


def load(name):
    return json.loads((EXAMPLE_DIR / name).read_text(encoding="utf-8"))


def load_schema(name):
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


SCHEMAS = {n: load_schema(f"{n}.schema.json") for n in ("space", "puzzle", "persona", "log", "npc", "baseline")}
REGISTRY = Registry().with_resources(
    (s["$id"], Resource.from_contents(s)) for s in SCHEMAS.values()
)
LOG_VALIDATOR = Draft202012Validator(SCHEMAS["log"], registry=REGISTRY)

SPACE = load("space.sample.json")
PUZZLES = load("puzzle.sample.json")
PERSONA = load("persona.sample.json")
TWO_FLOORS = load("space.two-floors.json")

REJECTIONS = [
    "출력이 JSON 형식이 아닙니다",
    "출력은 JSON 객체여야 합니다",
    "action은 문자열이어야 합니다",
    "알 수 없는 행동입니다. move, view, answer 중 하나를 쓰세요",
    "value는 문자열이어야 합니다",
    "칸 좌표 형식이 아닙니다",
    "지도에 없는 칸입니다",
    "존재하지 않는 사물입니다",
    "아직 가까이 가지 않은 사물입니다",
    "아직 퍼즐이 열리지 않았습니다",
    "답이 비어 있습니다",
    "answer에는 이유(reason)가 필요합니다",
]


def fresh(run_id="r1", **kw):
    return ge.new_game(copy.deepcopy(SPACE), copy.deepcopy(PUZZLES), copy.deepcopy(PERSONA),
                       run_id=run_id, model="muse-spark-1.3", **kw)


def sub(game, obj):
    return ge.submit(game, json.dumps(obj, ensure_ascii=False) if not isinstance(obj, str) else obj)


def answer(game, value, reason="테스트 이유"):
    return sub(game, {"action": "answer", "value": value, "reason": reason})


def last_error(game):
    return ge.observe(game)["observation"]["last_result"].get("error")


class NewGameTests(unittest.TestCase):
    def test_input_state_ignored_and_inputs_immutable(self):
        space = copy.deepcopy(SPACE)
        puzzles = copy.deepcopy(PUZZLES)
        persona = copy.deepcopy(PERSONA)
        game = ge.new_game(space, puzzles, persona, run_id="r1", model="muse-spark-1.3")
        self.assertEqual(ge.observe(game)["observation"]["opened_object_ids"], [])
        self.assertEqual(space, SPACE)  # #18 caller dicts unchanged
        self.assertEqual(puzzles, PUZZLES)
        self.assertEqual(persona, PERSONA)

    def test_defaults_for_omitted_optionals(self):
        # #28 rooms/start_instruction/max_attempts defaults
        space = copy.deepcopy(SPACE)
        del space["rooms"]
        puzzles = copy.deepcopy(PUZZLES)
        del puzzles["start_instruction"]
        del puzzles["puzzles"][0]["max_attempts"]
        game = ge.new_game(space, puzzles, copy.deepcopy(PERSONA), run_id="r1", model="m")
        self.assertEqual(ge.brief(game)["rooms"], [])
        self.assertIsNone(ge.observe(game)["observation"]["instruction"])
        sub(game, {"action": "move", "value": "E5"})
        sub(game, {"action": "view", "value": "desk@C4"})
        self.assertEqual(ge.observe(game)["observation"]["puzzle"]["attempts_left"], 5)

    def test_setup_error_on_broken_refs(self):
        bad = copy.deepcopy(PUZZLES)
        bad["space_id"] = "no-such-space"
        with self.assertRaises(ge.GameSetupError):
            ge.new_game(copy.deepcopy(SPACE), bad, copy.deepcopy(PERSONA), run_id="r1", model="m")
        bad2 = copy.deepcopy(PUZZLES)
        bad2["puzzles"][1]["object_id"] = "desk@C4"  # breaks chain continuity (M4)
        with self.assertRaises(ge.GameSetupError):
            ge.new_game(copy.deepcopy(SPACE), bad2, copy.deepcopy(PERSONA), run_id="r1", model="m")


class RejectionTests(unittest.TestCase):
    def test_all_twelve_messages_verbatim(self):
        game = fresh()
        cases = [
            ("", 1), ("   ", 1), ("{not json", 1),
            ("[1, 2]", 2), ('"str"', 2), ("42", 2), ("null", 2),
            ({"value": "x"}, 3), ({"action": 5, "value": "x"}, 3),
            ({"action": "jump", "value": "x"}, 4),
            ({"action": "move"}, 5), ({"action": "move", "value": 7}, 5),
            ({"action": "move", "value": "c4"}, 6),
            ({"action": "move", "value": "I1"}, 7),
            ({"action": "move", "value": "1F-C4"}, 7),  # #4 prefix rejected on single floor
            ({"action": "view", "value": "sofa@A1"}, 8),  # #5 missing object
            ({"action": "view", "value": "shelf@F2"}, 9),  # #5 locked object
            ({"action": "answer", "value": "apple", "reason": "r"}, 10),  # #6 pre-arrival
            ({"action": "answer", "value": "", "reason": "r"}, 10),  # arrival check first
            ({"action": "answer", "value": 5, "reason": "r"}, 5),
        ]
        for raw, idx in cases:
            with self.subTest(raw=raw):
                res = sub(game, raw) if isinstance(raw, str) else sub(game, raw)
                self.assertFalse(res["over"])
                ev = res["events"][-1]
                self.assertEqual(ev["type"], "rejected")
                self.assertEqual(ev["error"], REJECTIONS[idx - 1])
        # #11 empty answer after arrival; #12 reasonless answer
        sub(game, {"action": "move", "value": "E5"})
        sub(game, {"action": "view", "value": "desk@C4"})
        res = sub(game, {"action": "answer", "value": "", "reason": "r"})
        self.assertEqual(res["events"][-1]["error"], REJECTIONS[10])
        res = sub(game, {"action": "answer", "value": "apple"})
        self.assertEqual(res["events"][-1]["error"], REJECTIONS[11])
        res = sub(game, {"action": "answer", "value": "apple", "reason": ""})
        self.assertEqual(res["events"][-1]["error"], REJECTIONS[11])

    def test_attempted_action_values(self):
        game = fresh()
        res = ge.submit(game, "{bad")
        self.assertIsNone(res["events"][-1]["attempted_action"])
        res = sub(game, [1])
        self.assertIsNone(res["events"][-1]["attempted_action"])
        res = sub(game, {"action": "jump", "value": "x"})
        self.assertEqual(res["events"][-1]["attempted_action"], "jump")

    def test_rejection_consumes_no_attempt(self):
        game = fresh()  # #9 then correct -> attempt 1
        sub(game, {"action": "move", "value": "E5"})
        sub(game, {"action": "view", "value": "desk@C4"})
        sub(game, {"action": "answer", "value": "apple"})
        res = answer(game, " Apple ")
        ev = res["events"][0]
        self.assertEqual((ev["attempt"], ev["correct"]), (1, True))


class MovementArrivalTests(unittest.TestCase):
    def test_move_emits_no_dialogue_and_puzzle_null(self):
        game = fresh()  # #1
        res = sub(game, {"action": "move", "value": "C4"})
        self.assertEqual([e["type"] for e in res["events"]], ["move"])
        self.assertIsNone(ge.observe(game)["observation"]["puzzle"])

    def test_diagonal_arrival_opens(self):
        game = fresh()  # #2 move E5 (diagonal to D4) then view
        sub(game, {"action": "move", "value": "E5"})
        res = sub(game, {"action": "view", "value": "desk@C4"})
        self.assertEqual([e["type"] for e in res["events"]], ["view", "npc_dialogue"])
        self.assertEqual(res["events"][1]["npc"], "librarian")
        self.assertEqual(ge.observe(game)["observation"]["puzzle"]["attempts_left"], 5)

    def test_two_away_stays_closed(self):
        game = fresh()  # #3 move F4 opens nothing
        sub(game, {"action": "move", "value": "F4"})
        res = sub(game, {"action": "view", "value": "desk@C4"})
        self.assertEqual(res["events"][-1]["error"], REJECTIONS[8])
        res = sub(game, {"action": "view", "value": "shelf@F2"})
        self.assertEqual(res["events"][-1]["error"], REJECTIONS[8])

    def test_off_puzzle_view_has_no_dialogue(self):
        game = fresh()  # #7
        sub(game, {"action": "move", "value": "F2"})
        res = sub(game, {"action": "view", "value": "shelf@F2"})
        self.assertEqual([e["type"] for e in res["events"]], ["view"])
        self.assertIsNone(ge.observe(game)["observation"]["puzzle"])

    def test_two_floor_prefix_rules(self):
        space = copy.deepcopy(TWO_FLOORS)  # #19
        puzzles = {
            "puzzle_set_id": "two-set", "space_id": "sample-two-floors", "start_cell": "2F-A1",
            "puzzles": [{
                "number": 1, "object_id": "desk@2F-C2", "npc": "librarian",
                "dialogue": [{"text": "대화", "contains_hint": False}],
                "image": {"path": "p/1.jpg",
                          "sha256": "0" * 63 + "1"},
                "question": "Q", "answer": "apple", "answer_letter_count": 5,
                "hints": [{"level": 1, "after_wrong": 1, "text": "힌트"}],
                "next_instruction": None, "next_object_id": None,
            }],
        }
        game = ge.new_game(space, puzzles, copy.deepcopy(PERSONA), run_id="r1", model="m")
        res = sub(game, {"action": "move", "value": "C2"})
        self.assertEqual(res["events"][-1]["error"], REJECTIONS[6])
        res = sub(game, {"action": "move", "value": "2F-AA3"})
        self.assertEqual(res["events"][-1]["type"], "move")

    def test_duplicate_view_no_repeat_dialogue(self):
        game = fresh()  # #29
        sub(game, {"action": "move", "value": "E5"})
        sub(game, {"action": "view", "value": "desk@C4"})
        res = sub(game, {"action": "view", "value": "desk@C4"})
        self.assertEqual([e["type"] for e in res["events"]], ["view"])


class AnswerHintTests(unittest.TestCase):
    def test_whitespace_answer_counts_attempt_one(self):
        game = fresh()  # #8
        sub(game, {"action": "move", "value": "E5"})
        sub(game, {"action": "view", "value": "desk@C4"})
        res = answer(game, " Apple ")
        ev_ans, ev_end = res["events"]
        self.assertEqual(ev_ans["type"], "answer_submitted")
        self.assertEqual((ev_ans["value"], ev_ans["attempt"], ev_ans["correct"]), (" Apple ", 1, True))
        self.assertEqual((ev_end["type"], ev_end["result"]), ("puzzle_ended", "solved_by_dialogue"))
        self.assertEqual(ge.observe(game)["observation"]["instruction"], "F2의 선반으로 가라")

    def test_one_wrong_reveals_hint(self):
        game = fresh()  # #10
        sub(game, {"action": "move", "value": "E5"})
        sub(game, {"action": "view", "value": "desk@C4"})
        res = answer(game, "pear")
        self.assertEqual([(e["type"], e.get("level")) for e in res["events"]],
                         [("answer_submitted", None), ("hint_revealed", 1)])
        obs = ge.observe(game)["observation"]
        self.assertEqual(obs["puzzle"]["attempts_left"], 4)
        self.assertEqual(obs["puzzle"]["hints"], [{"level": 1, "text": "가상 힌트 1"}])

    def test_wrong_then_right_is_with_hint(self):
        game = fresh()  # #11
        sub(game, {"action": "move", "value": "E5"})
        sub(game, {"action": "view", "value": "desk@C4"})
        answer(game, "pear")
        res = answer(game, "apple")
        self.assertEqual(res["events"][-1]["result"], "solved_with_hint")


class FailAdvanceTests(unittest.TestCase):
    def test_five_wrongs_fail_and_advance(self):
        game = fresh()  # #12
        sub(game, {"action": "move", "value": "E5"})
        sub(game, {"action": "view", "value": "desk@C4"})
        for i in range(4):
            answer(game, f"wrong{i}")
        res = answer(game, "wrong4")
        types = [e["type"] for e in res["events"]]
        self.assertEqual(types, ["answer_submitted", "puzzle_ended"])
        self.assertEqual(res["events"][-1]["result"], "failed")
        obs = ge.observe(game)["observation"]
        self.assertEqual(obs["instruction"], "F2의 선반으로 가라")
        self.assertEqual(obs["last_result"].get("answer"), "apple")  # one-time reveal
        obs2 = ge.observe(game)["observation"]
        self.assertNotIn("answer", obs2["last_result"])  # shown only once
        self.assertIsNone(obs2["puzzle"])  # next puzzle not yet arrived

    def test_last_puzzle_fail_completes(self):
        game = fresh()  # #13
        sub(game, {"action": "move", "value": "E5"})
        sub(game, {"action": "view", "value": "desk@C4"})
        answer(game, "apple")
        sub(game, {"action": "move", "value": "F2"})
        sub(game, {"action": "view", "value": "shelf@F2"})
        for i in range(4):
            answer(game, f"wrong{i}")
        res = answer(game, "wrong4")
        self.assertEqual([e["type"] for e in res["events"]],
                         ["answer_submitted", "puzzle_ended", "end"])
        self.assertEqual(res["events"][-1]["outcome"], "completed")
        self.assertTrue(res["over"])

    def test_completion_on_limit_action_still_completed(self):
        game = fresh(max_actions=6)  # #16
        sub(game, {"action": "move", "value": "E5"})
        sub(game, {"action": "view", "value": "desk@C4"})
        answer(game, "apple")
        sub(game, {"action": "move", "value": "F2"})
        sub(game, {"action": "view", "value": "shelf@F2"})
        res = answer(game, "pineapple")  # 6th action at limit 6
        self.assertEqual(res["events"][-1], {"t": 11, "puzzle": 2, "type": "end", "outcome": "completed"})


def solve_both(game):
    sub(game, {"action": "move", "value": "E5"})
    sub(game, {"action": "view", "value": "desk@C4"})
    answer(game, "apple")
    sub(game, {"action": "move", "value": "F2"})
    sub(game, {"action": "view", "value": "shelf@F2"})
    return answer(game, "pineapple")


class LogShapeTests(unittest.TestCase):
    def test_full_walkthrough_to_log(self):
        game = fresh()  # #14
        solve_both(game)
        log = ge.to_log(game)
        self.assertEqual(
            [(e["t"], e["type"]) for e in log["events"]],
            [(1, "move"), (2, "view"), (3, "npc_dialogue"), (4, "answer_submitted"),
             (5, "puzzle_ended"), (6, "move"), (7, "view"), (8, "npc_dialogue"),
             (9, "answer_submitted"), (10, "puzzle_ended"), (11, "end")],
        )
        self.assertEqual(
            (log["run_id"], log["puzzle_set_id"], log["model"], log["persona"]),
            ("r1", "sample-set", "muse-spark-1.3", PERSONA),
        )
        self.assertNotIn("seed", log)
        game2 = fresh(run_id="r2", seed=7)
        solve_both(game2)
        self.assertEqual(ge.to_log(game2)["seed"], 7)

    def test_fifty_rejections_then_action_limit(self):
        game = fresh()  # #15 default max_actions 50
        for _ in range(50):
            res = ge.submit(game, "{bad")
        self.assertEqual(res["events"][-1], {"t": 51, "puzzle": 1, "type": "end", "outcome": "action_limit"})
        self.assertTrue(res["over"])
        log = ge.to_log(game)
        self.assertEqual(len(log["events"]), 51)
        self.assertTrue(all(e["type"] == "rejected" for e in log["events"][:50]))


class AbortGuardTests(unittest.TestCase):
    def test_abort_yields_only_api_error(self):
        game = fresh()
        sub(game, {"action": "move", "value": "E5"})
        before = len(game.events)
        res = ge.abort(game)
        self.assertEqual(len(game.events), before + 1)
        self.assertEqual(res["events"][-1]["outcome"], "api_error")
        self.assertTrue(res["over"])

    def test_post_end_calls_raise(self):
        game = fresh()
        solve_both(game)
        with self.assertRaises(ge.GameStateError):
            sub(game, {"action": "move", "value": "A1"})
        with self.assertRaises(ge.GameStateError):
            ge.observe(game)
        with self.assertRaises(ge.GameStateError):
            ge.abort(game)
        game2 = fresh()
        with self.assertRaises(ge.GameStateError):
            ge.to_log(game2)


class ReplayTests(unittest.TestCase):
    def test_two_objects_open_at_once(self):
        game = fresh()  # #20 E3 touches desk (D4) and shelf (F2) diagonally
        sub(game, {"action": "move", "value": "E3"})
        opened = ge.observe(game)["observation"]["opened_object_ids"]
        self.assertEqual(sorted(opened), ["desk@C4", "shelf@F2"])
        res = sub(game, {"action": "view", "value": "desk@C4"})
        self.assertEqual([e["type"] for e in res["events"]], ["view", "npc_dialogue"])

    def test_start_cell_variant(self):
        puzzles = copy.deepcopy(PUZZLES)  # #21 start next to nothing
        puzzles["start_cell"] = "H6"
        game = ge.new_game(copy.deepcopy(SPACE), puzzles, copy.deepcopy(PERSONA),
                           run_id="r1", model="m")
        res = sub(game, {"action": "view", "value": "desk@C4"})
        self.assertEqual(res["events"][-1]["error"], REJECTIONS[8])
        sub(game, {"action": "move", "value": "E5"})
        sub(game, {"action": "view", "value": "desk@C4"})
        answer(game, "apple")
        sub(game, {"action": "move", "value": "F2"})
        sub(game, {"action": "view", "value": "shelf@F2"})
        res = answer(game, "pineapple")
        self.assertEqual(res["events"][-1]["outcome"], "completed")

    def test_hint_condition_variant(self):
        puzzles = copy.deepcopy(PUZZLES)  # #22 hint opens after 2 wrongs
        puzzles["puzzles"][0]["hints"][0]["after_wrong"] = 2
        game = ge.new_game(copy.deepcopy(SPACE), puzzles, copy.deepcopy(PERSONA),
                           run_id="r1", model="m")
        sub(game, {"action": "move", "value": "E5"})
        sub(game, {"action": "view", "value": "desk@C4"})
        res = answer(game, "pear")
        self.assertEqual([e["type"] for e in res["events"]], ["answer_submitted"])
        res = answer(game, "plum")
        self.assertEqual(res["events"][-1], {"t": 6, "puzzle": 1, "type": "hint_revealed", "level": 1})

    def test_turn_order_view_first(self):
        game = fresh()  # #23 distant open-then-view still needs arrival
        sub(game, {"action": "move", "value": "E3"})
        res = sub(game, {"action": "view", "value": "shelf@F2"})
        self.assertEqual([e["type"] for e in res["events"]], ["view"])
        res = sub(game, {"action": "view", "value": "desk@C4"})
        self.assertEqual([e["type"] for e in res["events"]], ["view", "npc_dialogue"])


class OutcomeTaxonomyTests(unittest.TestCase):
    def test_three_results(self):
        g1 = fresh(run_id="r1")
        sub(g1, {"action": "move", "value": "E5"})
        sub(g1, {"action": "view", "value": "desk@C4"})
        res = answer(g1, "apple")
        self.assertEqual((res["events"][-1]["result"], res["events"][-1]["attempts_used"]),
                         ("solved_by_dialogue", 1))
        g2 = fresh(run_id="r2")
        sub(g2, {"action": "move", "value": "E5"})
        sub(g2, {"action": "view", "value": "desk@C4"})
        answer(g2, "pear")
        res = answer(g2, "apple")
        self.assertEqual((res["events"][-1]["result"], res["events"][-1]["attempts_used"]),
                         ("solved_with_hint", 2))


class ExposureTests(unittest.TestCase):
    # Forbidden keys (exact JSON keys; opened_object_ids is allowed and contains
    # "object_id" as a substring, so match with quotes) and forbidden values.
    BANNED_KEYS = ["next_object_id", "next_instruction", "object_id", "photos", "path",
                   "sha256", "contains_hint", "after_wrong", "npc", "tone",
                   "on_wrong", "on_correct"]
    BANNED_VALUES = ["librarian", "가상 오답 대사", "가상 정답 대사", "desk_front",
                     "puzzles/sample"]

    def assertClean(self, text):
        for key in self.BANNED_KEYS:
            self.assertNotIn(f'"{key}"', text)
        for token in self.BANNED_VALUES:
            self.assertNotIn(token, text)

    def test_brief_and_observation_hide_forbidden_fields(self):
        game = fresh()
        brief_text = json.dumps(ge.brief(game), ensure_ascii=False)
        self.assertClean(brief_text)
        self.assertFalse(ge.brief(game)["cell_prefix_required"])
        sub(game, {"action": "move", "value": "E5"})
        obs_text = json.dumps(ge.observe(game)["observation"], ensure_ascii=False)
        self.assertNotIn("apple", obs_text)
        sub(game, {"action": "view", "value": "desk@C4"})
        obs_text = json.dumps(ge.observe(game)["observation"], ensure_ascii=False)
        self.assertClean(obs_text)
        self.assertIn("가상 대화 1", obs_text)  # current puzzle dialogue visible
        self.assertNotIn("가상 대화 2", obs_text)  # other puzzle dialogue hidden

    def test_images_only_current_puzzle_and_last_view(self):
        game = fresh()
        self.assertEqual(ge.observe(game)["images"], [])
        sub(game, {"action": "move", "value": "E5"})
        sub(game, {"action": "view", "value": "desk@C4"})
        images = ge.observe(game)["images"]
        self.assertIn("puzzles/sample_1.jpg", images)
        self.assertIn("desk_front.jpg", images)

    def test_to_log_passes_log_schema(self):
        game = fresh()
        solve_both(game)
        errors = list(LOG_VALIDATOR.iter_errors(ge.to_log(game)))
        self.assertEqual([e.message for e in errors], [])
        game2 = fresh()
        for _ in range(50):
            ge.submit(game2, "{bad")
        errors = list(LOG_VALIDATOR.iter_errors(ge.to_log(game2)))
        self.assertEqual([e.message for e in errors], [])


if __name__ == "__main__":
    unittest.main()

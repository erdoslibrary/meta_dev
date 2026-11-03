"""Report aggregation tests on fixture logs. No model, no network."""

import unittest

from realtosim import report

PUZZLE_SET = {"puzzles": [{"number": 1}]}


def ended(result, attempts):
    return {"t": 1, "puzzle": 1, "type": "puzzle_ended",
            "result": result, "attempts_used": attempts}


def fixture_logs():
    events = []
    for _ in range(4):
        events.append(ended("solved_by_dialogue", 1))
    for _ in range(3):
        events.append(ended("solved_with_hint", 3))
    for _ in range(3):
        events.append(ended("failed", 5))
    return [{"run_id": "r01", "persona": {}, "puzzle_set_id": "s",
             "model": "m",
             "events": events + [{"t": 2, "puzzle": 1,
                                  "type": "end", "outcome": "completed"}]}]


class ReportTests(unittest.TestCase):
    def test_numbers(self):
        agg = report.aggregate(fixture_logs(), PUZZLE_SET)
        row = agg["puzzles"][1]
        self.assertEqual(row["ended"], 10)
        self.assertAlmostEqual(row["avg_score"], 2.1)
        self.assertAlmostEqual(row["fail_rate"], 0.3)
        self.assertAlmostEqual(row["hint_rate"], 0.3)
        self.assertAlmostEqual(row["first_try_rate"], 0.4)

    def test_controversial(self):  # both rates >= 30%
        agg = report.aggregate(fixture_logs(), PUZZLE_SET)
        self.assertTrue(agg["puzzles"][1]["controversial"])

    def test_not_controversial_when_low_fail(self):
        logs = [{"run_id": "r01", "persona": {}, "puzzle_set_id": "s",
                 "model": "m",
                 "events": [ended("solved_by_dialogue", 1),
                            {"t": 2, "puzzle": 1,
                             "type": "end", "outcome": "completed"}]}]
        agg = report.aggregate(logs, PUZZLE_SET)
        self.assertFalse(agg["puzzles"][1]["controversial"])

    def test_render_has_all_sections(self):
        agg = report.aggregate(fixture_logs(), PUZZLE_SET)
        text = report.render("s", {"puzzles": [{"number": 1}]},
                             {"observations": []}, agg, "판정: 통과", None)
        for section in ("## 난이도 표", "## 갈리는 문제", "## 상위 오답과 이유",
                        "## 모델 분석", "## 오프라인 관찰과 나란히", "## 한계"):
            self.assertIn(section, text)
        self.assertIn("분석 없음", text)


if __name__ == "__main__":
    unittest.main()

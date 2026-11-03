"""Oracle: a player that knows every answer walks puzzle 1..N (TRD §5, M12).

Usage: python -m realtosim.oracle <set> [--data data --logs logs]
Exit 0 only when every puzzle ends solved_by_dialogue and the run completes.
"""

import argparse
import json
import sys
from pathlib import Path

from realtosim import game_engine
from realtosim.validate import load_json

ORACLE_PERSONA = {
    "age": 30,
    "job": "oracle",
    "vocab": "중",
    "thinking": "문자 그대로 읽음",
}


def _first_cell(object_id):
    """An object cell to stand on: range start, prefix kept."""
    cells = object_id.split("@", 1)[1]
    return cells.split(":", 1)[0]


def run(data_dir, set_id):
    """Play the whole set with known answers. Returns the run log."""
    data_dir = Path(data_dir)
    space = load_json(data_dir / "space.json")
    puzzle_set = load_json(data_dir / "puzzle.json")
    game = game_engine.new_game(space, puzzle_set, ORACLE_PERSONA,
                                run_id="r0", model="oracle")
    for puzzle in puzzle_set["puzzles"]:
        game_engine.submit(game, json.dumps(
            {"action": "move", "value": _first_cell(puzzle["object_id"]),
             "reason": "oracle: move to object"}))
        game_engine.submit(game, json.dumps(
            {"action": "view", "value": puzzle["object_id"],
             "reason": "oracle: view object"}))
        result = game_engine.submit(game, json.dumps(
            {"action": "answer", "value": puzzle["answer"],
             "reason": "oracle: known answer"}))
        if game.over:
            break
    return game_engine.to_log(game)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Oracle walkthrough (TRD M12).")
    parser.add_argument("set", help="puzzle_set_id, equals directory name")
    parser.add_argument("--data", default="data")
    parser.add_argument("--logs", default="logs")
    args = parser.parse_args(argv)
    log = run(Path(args.data) / args.set, args.set)
    out = Path(args.logs) / args.set / "oracle" / "r0.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    ended = [e for e in log["events"] if e["type"] == "puzzle_ended"]
    ok = (log["events"][-1].get("outcome") == "completed"
          and all(e["result"] == "solved_by_dialogue" for e in ended)
          and len(ended) > 0)
    print(f"oracle: {len(ended)} puzzles, "
          f"last={log['events'][-1].get('type')}/{log['events'][-1].get('outcome')}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
